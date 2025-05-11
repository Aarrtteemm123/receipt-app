from fastapi import APIRouter
from receipt_app.api import ReceiptApi

api_router = APIRouter()

receipt_api = ReceiptApi()

api_router.add_api_route("/create-receipt", receipt_api.create_receipt, methods=["POST"])
