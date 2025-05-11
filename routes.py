from fastapi import APIRouter
from login_app.routes import api_router as login_api_routes
from receipt_app.routes import api_router as receipt_api_routes

api_router = APIRouter()


api_router.include_router(login_api_routes)
api_router.include_router(receipt_api_routes)
