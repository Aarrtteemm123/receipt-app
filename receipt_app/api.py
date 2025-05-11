from fastapi import Request

from auth_jwt.decorators import login_required


class ReceiptApi:

    @login_required
    async def create(self, request: Request):
        return {}
