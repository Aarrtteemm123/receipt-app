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
    with TestClient(app) as client:
        yield client

@pytest.mark.asyncio
async def test_register(client):
    response = client.post("/api/register", json={
        "name": "testuser",
        "username": "testuser",
        "password": "testpass"
    })
    assert response.status_code == 200

