from fastapi import Request, Response

from auth_jwt.decorators import login_required
from login_app.services.login_svc import LoginSvc
from general_services.redis_svc import RedisSvc
from login_app.dto import LoginUserDto, NewUserDto
from models import User


class LoginApi:
    def __init__(self):
        self.login_svc = LoginSvc()
        self.redis_svc = RedisSvc()

    async def login(self, request: Request, data: LoginUserDto):
        response = await self.login_svc.login(data.username, data.password)
        return response

    async def register(self, request: Request, data: NewUserDto):
        user = User(**data.model_dump(exclude=["password"]))
        user.set_password(data.password)
        await user.save()
        return Response(content=f"New user has been registered")

    @login_required
    async def refresh_token(self, request: Request):
        refresh_token = request.cookies.get("refresh_token")
        response = await self.login_svc.refresh_token(refresh_token)
        return response

    @login_required
    async def logout(self, request: Request):
        resp = await self.login_svc.logout(request, "/api/login")
        return resp
