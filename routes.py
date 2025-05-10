from fastapi import APIRouter
from login_app.routes import api_router as login_api_routes

api_router = APIRouter()


api_router.include_router(login_api_routes)
