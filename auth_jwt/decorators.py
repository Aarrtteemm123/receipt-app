from functools import wraps

from fastapi import Request
from fastapi.responses import RedirectResponse
from auth_jwt.helpers import get_current_user
from general_services.redis_svc import RedisSvc
from models import User


def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request")
        token_data = await get_current_user(request)
        if not token_data:
            return RedirectResponse(url="/login")

        request.state.user = await User.get(id=token_data.user_id)
        if not request.state.user.is_active:
            redis_svc = RedisSvc()
            redis_svc.delete(request.state.user.id)
            return RedirectResponse(url="/login")

        return await func(*args, **kwargs)

    return wrapper

