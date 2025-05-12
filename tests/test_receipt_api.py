import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tortoise import Tortoise
from decimal import Decimal
import logging

# Налаштування логування Tortoise ORM
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
from apps.login_app.routes import api_router as login_api_router
from apps.receipt_app.routes import api_router as receipt_api_router

from models import User, Receipt, PaymentType
from enums import PaymentTypeEnum

TORTOISE_TEST_DB = {
    "connections": {"default": "sqlite://:memory:"},
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        }
    },
}

@pytest.fixture(scope="module")
async def init_tortoise():
    """Ініціалізує Tortoise ORM та створює схему бази даних для тестів."""
    logger.info("Initializing Tortoise ORM...")
    try:
        await Tortoise.init(config=TORTOISE_TEST_DB)
        logger.info("Tortoise ORM initialized.")
        logger.info("Generating database schemas...")
        await Tortoise.generate_schemas(safe=True)
        logger.info("Database schemas generated.")

        logger.info("Creating initial payment types...")
        await PaymentType.get_or_create(name=PaymentTypeEnum.CASH)
        await PaymentType.get_or_create(name=PaymentTypeEnum.CREDIT_CART)
        logger.info("Payment types created.")

        yield
    except Exception as e:
        logger.error(f"Error during Tortoise ORM initialization: {e}", exc_info=True)
        pytest.fail(f"Failed to initialize Tortoise ORM: {e}")
    finally:
        logger.info("Closing Tortoise ORM connections...")
        await Tortoise.close_connections()
        logger.info("Tortoise ORM connections closed.")


@pytest.fixture(scope="module")
async def client(init_tortoise):
    """Створює тестовий клієнт для FastAPI додатка."""
    app = FastAPI()
    app.include_router(login_api_router, prefix="/api")
    app.include_router(receipt_api_router, prefix="/api")

    with TestClient(app, raise_server_exceptions=True) as client:
        yield client

@pytest.fixture(scope="module")
async def test_user():
    """Створює тестового користувача в базі даних."""
    username = "test_user_for_receipts"
    user = await User.get_or_none(username=username)
    if not user:
        user = User(name="Test User", username=username)
        user.set_password("securepassword")
        await user.save()
    return user


@pytest.fixture
async def authenticated_client(client, test_user):
    """
    Виконує реєстрацію та авторизацію через API для тестового користувача
    та повертає тестовий клієнт з встановленими токенами авторизації.
    """
    login_data = {
        "username": test_user.username,
        "password": "securepassword"
    }
    login_response = client.post("/api/login", json=login_data)

    assert login_response.status_code == 200
    login_response_json = login_response.json()

    access_token = login_response_json.get("access_token")
    refresh_token = login_response.cookies.get("refresh_token")

    assert access_token is not None
    client.headers["Authorization"] = f"Bearer {access_token}"

    if refresh_token:
        client.cookies.set("refresh_token", refresh_token)

    yield client

    client.headers.pop("Authorization", None)
    client.cookies.delete("refresh_token")
    client.cookies.delete("access_token")


@pytest.mark.asyncio
async def test_create_receipt_success(authenticated_client):
    """Тестує успішне створення чека авторизованим користувачем."""
    receipt_data = {
        "products": [
            {"name": "Product A", "price": 10.50, "quantity": 2},
            {"name": "Product B", "price": 5.00, "quantity": 1.5}
        ],
        "payment": {
            "type": PaymentTypeEnum.CASH,
            "amount": 30.00
        }
    }
    response = authenticated_client.post("/api/create-receipt", json=receipt_data)

    assert response.status_code == 200
    response_json = response.json()

    # Перевірка структури відповіді
    assert isinstance(response_json, dict)
    assert "id" in response_json
    assert "products" in response_json
    assert "payment" in response_json
    assert "total" in response_json
    assert "rest" in response_json
    assert "created_at" in response_json

    # Перевірка значень
    expected_total = Decimal(10.50) * Decimal(2) + Decimal(5.00) * Decimal(1.5)
    expected_rest = Decimal(30.00) - expected_total

    assert Decimal(str(response_json["total"])) == expected_total.quantize(Decimal('0.01'))
    assert Decimal(str(response_json["payment"]["amount"])) == Decimal(30.00).quantize(Decimal('0.01'))
    assert response_json["payment"]["type"] == PaymentTypeEnum.CASH
    assert Decimal(str(response_json["rest"])) == expected_rest.quantize(Decimal('0.01'))
    assert len(response_json["products"]) == 2
    assert response_json["products"][0]["name"] == "Product A"
    assert Decimal(str(response_json["products"][0]["total"])) == (Decimal(10.50) * Decimal(2)).quantize(Decimal('0.01'))
    assert response_json["products"][1]["name"] == "Product B"
    assert Decimal(str(response_json["products"][1]["total"])) == (Decimal(5.00) * Decimal(1.5)).quantize(Decimal('0.01'))

    receipt_in_db = await Receipt.get(id=response_json["id"]).prefetch_related("products", "payment_type")
    assert receipt_in_db is not None
    assert Decimal(str(receipt_in_db.total)) == expected_total.quantize(Decimal('0.01'))
    assert len(receipt_in_db.products) == 2
    assert receipt_in_db.payment_type.name == PaymentTypeEnum.CASH


@pytest.mark.asyncio
async def test_create_receipt_insufficient_payment(authenticated_client):
    """Тестує створення чека з недостатньою сумою оплати."""
    receipt_data = {
        "products": [
            {"name": "Product C", "price": 20.00, "quantity": 1}
        ],
        "payment": {
            "type": PaymentTypeEnum.CREDIT_CART,
            "amount": 15.00
        }
    }
    response = authenticated_client.post("/api/create-receipt", json=receipt_data)

    assert response.status_code == 400
    response_json = response.json()
    assert response_json.get("detail") == "Insufficient payment amount"

@pytest.mark.asyncio
async def test_get_receipt_by_id_not_found(authenticated_client):
    """Тестує спробу отримання неіснуючого чека за ID."""
    response = authenticated_client.get("/api/get-receipt/99999")

    assert response.status_code == 404
    response_json = response.json()
    assert response_json.get("detail") in ["Receipt not found", "Not Found"]

@pytest.mark.asyncio
async def test_get_receipt_text_not_found(authenticated_client):
    """Тестує спробу отримання текстового представлення неіснуючого чека."""
    response = authenticated_client.get("/api/get-receipt-text/99999/text")

    assert response.status_code == 404
    response_json = response.json()
    assert response_json.get("detail") in ["Receipt not found", "Not Found"]


