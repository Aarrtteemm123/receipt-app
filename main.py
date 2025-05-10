from fastapi import FastAPI, Request
from config import init_db_connect
from routes import api_router as api_routes

app = FastAPI()

app.include_router(api_routes, prefix="/api")


@app.get("/healthcheck")
async def healthcheck(request: Request):
    await init_db_connect()
    return {"status": "app server is running, db connection ok..."}
