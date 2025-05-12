from os import access

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tortoise import Tortoise
from apps.login_app.routes import api_router as login_api_router

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
    await Tortoise.init(config=TORTOISE_TEST_DB)
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture(scope="module")
def client(init_tortoise):
    app = FastAPI()
    app.include_router(login_api_router, prefix="/api")
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.mark.asyncio
async def test_register_success(client):
    """Тестує успішну реєстрацію нового користувача."""
    user_data = {
        "name": "testuser",
        "username": "testuser_reg",
        "password": "testpass"
    }
    response = client.post("/api/register", json=user_data)
    assert response.status_code == 200
    assert response.text == "New user has been registered"


@pytest.mark.asyncio
async def test_register_existing_user(client):
    """Тестує спробу реєстрації користувача з вже існуючим іменем користувача."""
    user_data = {
        "name": "existinguser",
        "username": "existing_user_reg",
        "password": "password123"
    }
    client.post("/api/register", json=user_data)  # Перша успішна реєстрація

    response = client.post("/api/register", json=user_data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client):
    """Тестує успішну авторизацію користувача."""
    register_data = {
        "name": "loginuser",
        "username": "login_user_test",
        "password": "loginpass"
    }
    client.post("/api/register", json=register_data)

    login_data = {
        "username": register_data["username"],
        "password": register_data["password"]
    }
    response = client.post("/api/login", json=login_data)
    response_json = response.json()

    assert response.status_code == 200
    assert "access_token" in response_json
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_login_incorrect_password(client):
    """Тестує спробу авторизації з невірним паролем."""
    register_data = {
        "name": "wrongpassuser",
        "username": "wrong_pass_test",
        "password": "correctpassword"
    }
    client.post("/api/register", json=register_data)

    login_data = {
        "username": register_data["username"],
        "password": "incorrectpassword"
    }
    response = client.post("/api/login", json=login_data)

    assert response.status_code == 401
    assert "Wrong username or password" in response.text


@pytest.mark.asyncio
async def test_login_non_existent_user(client):
    """Тестує спробу авторизації з неіснуючим іменем користувача."""
    login_data = {
        "username": "non_existent_user",
        "password": "somepassword"
    }
    response = client.post("/api/login", json=login_data)

    assert response.status_code == 401
    assert "Wrong username or password" in response.text


@pytest.mark.asyncio
async def test_refresh_token_success(client):
    """Тестує успішне оновлення токена."""
    register_data = {
        "name": "refreshuser",
        "username": "refresh_token_test",
        "password": "refreshpass"
    }
    client.post("/api/register", json=register_data)
    login_data = {
        "username": register_data["username"],
        "password": register_data["password"]
    }
    login_response = client.post("/api/login", json=login_data)
    access_token = login_response.json()["access_token"]

    refresh_token = login_response.cookies.get("refresh_token")
    assert refresh_token is not None

    client.cookies.set("refresh_token", refresh_token)
    response = client.post(
        "/api/refresh",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_refresh_token_invalid(client):
    """Тестує спробу оновлення токена з недійсним refresh token."""
    register_data = {
        "name": "refreshuser",
        "username": "refresh_token_test",
        "password": "refreshpass"
    }
    client.post("/api/register", json=register_data)

    login_data = {
        "username": register_data["username"],
        "password": register_data["password"]
    }
    login_response = client.post("/api/login", json=login_data)

    access_token = login_response.json()["access_token"]
    client.cookies.set("refresh_token", "Invalid_refresh_token")
    response = client.post(
        "/api/refresh",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 401

