import datetime
from typing import Optional

import jwt
from fastapi import HTTPException, status
from jwt import DecodeError, ExpiredSignatureError, InvalidIssuerError

from config import ALGORITHM, ISSUER, TOKEN_SECRET_KEY
from enums import TokenTypeEnum
from general_services.redis_svc import RedisSvc


class TokenSvc:
    def __init__(self):
        self.redis_svc = RedisSvc()

    def create_access_token(
        self, data: dict, expires_delta: Optional[datetime.timedelta]
    ):
        access_token = self._create_token(data, expires_delta)
        return access_token

    def create_refresh_token(
        self, data: dict, expires_delta: Optional[datetime.timedelta] = None
    ):
        refresh_token = self._create_token(data, expires_delta)
        return refresh_token

    def _create_token(self, data: dict, expires_delta: Optional[datetime.timedelta]):
        to_encode = data.copy()
        expire = datetime.datetime.now(datetime.UTC) + expires_delta
        to_encode.update({"exp": expire, "iss": ISSUER})
        encoded_jwt = jwt.encode(to_encode, TOKEN_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str, type_: TokenTypeEnum = None):
        try:
            payload = jwt.decode(
                token,
                TOKEN_SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"verify_exp": True, "verify_iat": True},
                issuer=ISSUER,
            )

            auth = self.redis_svc.hget(payload["user_id"], "auth")

            if not auth or (type_ == TokenTypeEnum.ACCESS and token != auth.get("access_token")):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Fake or non-working token",
                )

            if not auth or (type_ == TokenTypeEnum.REFRESH and token != auth.get("refresh_token")):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Fake or non-working token",
                )

            return payload
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except InvalidIssuerError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")
        except DecodeError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
