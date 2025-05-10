from fastapi import APIRouter

from auth_jwt.dto import TokenDto
from login_app.api import LoginApi

api_router = APIRouter()

login_api = LoginApi()

api_router.add_api_route("/login", login_api.login, methods=["POST"], response_model=TokenDto)
api_router.add_api_route("/register", login_api.register, methods=["POST"])
api_router.add_api_route("/refresh", login_api.refresh_token, methods=["POST"], response_model=TokenDto)
api_router.add_api_route("/logout", login_api.logout, methods=["POST"])
