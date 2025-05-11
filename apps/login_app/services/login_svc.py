import datetime
import os

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.requests import Request
from auth_jwt.services.token_svc import TokenSvc
from config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from enums import TokenTypeEnum
from general_services.redis_svc import RedisSvc
from models import User


class LoginSvc:
    def __init__(self):
        self.token_svc = TokenSvc()
        self.redis_svc = RedisSvc()

    async def login(self, username: str, password: str):
        user = await User.get_or_none(username=username)
        if not user or not user.check_password(password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Wrong username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is not active",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        payload_access_token = {
            "sub": username,
            "user_id": user.id,
        }
        payload_refresh_token = {
            "sub": username,
            "user_id": user.id,
        }
        access_token = self.token_svc.create_access_token(
            data=payload_access_token, expires_delta=access_token_expires
        )
        refresh_token = self.token_svc.create_refresh_token(
            data=payload_refresh_token, expires_delta=refresh_token_expires
        )
        data = {
            "access_token": access_token,
            "token_type": "bearer",
        }
        response = JSONResponse(content=data)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,  # Prevent client-side JavaScript from accessing the token
            max_age=int(refresh_token_expires.total_seconds()),  # Set cookie expiration
            expires=int(refresh_token_expires.total_seconds()),
            secure=(
                True if os.getenv("ENV") == "prod" else False
            ),  # Set True in production (for HTTPS)
            samesite="strict",  # Adjust as per your use case
        )
        auth = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        self.redis_svc.hset(user.id, "auth", auth)

        # Return the access token in the response body
        return response

    async def refresh_token(self, refresh_token: str):
        payload = self.token_svc.verify_token(refresh_token, TokenTypeEnum.REFRESH)
        access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        new_payload_access_token = {
            "sub": payload.get("sub"),
            "user_id": payload.get("user_id"),
        }
        new_payload_refresh_token = {
            "sub": payload.get("sub"),
            "user_id": payload.get("user_id"),
        }
        access_token = self.token_svc.create_access_token(
            data=new_payload_access_token, expires_delta=access_token_expires
        )
        refresh_token = self.token_svc.create_refresh_token(
            data=new_payload_refresh_token, expires_delta=refresh_token_expires
        )

        data = {"access_token": access_token, "token_type": "Bearer"}

        response = JSONResponse(content=data)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,  # Prevent client-side JavaScript from accessing the token
            max_age=int(refresh_token_expires.total_seconds()),  # Set cookie expiration
            secure=(
                True if os.getenv("ENV") == "prod" else False
            ),  # Set True in production (for HTTPS)
            samesite="strict",  # Adjust as per your use case
        )
        auth = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        self.redis_svc.hset(payload.get("user_id"), "auth", auth)
        # Return the access token in the response body
        return response

    async def logout(self, request: Request, redirect_route):
        user = request.state.user
        response = RedirectResponse(url=redirect_route)
        response.delete_cookie("refresh_token")
        self.redis_svc.delete(user.id)
        return response
