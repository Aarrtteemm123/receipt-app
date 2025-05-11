from fastapi.security import OAuth2PasswordBearer
from auth_jwt.dto import TokenDataDto
from auth_jwt.services.token_svc import TokenSvc
from enums import TokenTypeEnum

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth", auto_error=False)


async def get_current_user(request):
    token_svc = TokenSvc()
    token = await oauth2_scheme(request)
    if not token:
        return None
    try:
        payload = token_svc.verify_token(token, TokenTypeEnum.ACCESS)
        user_id = payload.get("user_id")
        if user_id is None:
            return None
        return TokenDataDto(user_id=user_id)
    except Exception:
        return None
