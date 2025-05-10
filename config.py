import asyncio
import logging
import os

import redis
from dotenv import load_dotenv
from tortoise import Tortoise

logging.basicConfig(level=logging.INFO)

load_dotenv()

# LOGIN
TOKEN_SECRET_KEY = os.getenv("TOKEN_SECRET_KEY", "your-token-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 5))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 5))
ISSUER = os.getenv("ISSUER", "issuer")

# DATABASE
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST")

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

TORTOISE_ORM = {
    "connections": {
        "default": f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    },
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        }
    },
}


async def init_db_connect():
    await Tortoise.init(config=TORTOISE_ORM)
    result = await Tortoise.get_connection("default").execute_query("SELECT 1")
    logging.info(f"Test query result: {result and result[1][0]['?column?'] == 1}")
    logging.info("Connected to the database")
