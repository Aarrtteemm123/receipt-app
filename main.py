from fastapi import FastAPI, Request, Response
from config import init_db_connect
from dto import NewUserDto
from models import User

app = FastAPI()


@app.get("/healthcheck")
async def healthcheck(request: Request):
    await init_db_connect()
    return {"status": "app server is running, db connection ok..."}

@app.post("/register")
async def register(request: Request, data: NewUserDto):
    user = User(**data.model_dump(exclude=["password"]))
    user.set_password(data.password)
    await user.save()
    return Response(content=f"New user has been registered")
