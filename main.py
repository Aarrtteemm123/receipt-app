from fastapi import FastAPI, Request
from config import init_db_connect

app = FastAPI()


@app.get("/healthcheck")
async def healthcheck(request: Request):
    await init_db_connect()
    return {"status": "app server is running, db connection ok..."}
