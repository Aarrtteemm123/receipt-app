from fastapi import APIRouter
from apps.receipt_app.api import ReceiptApi
from fastapi.responses import PlainTextResponse

api_router = APIRouter()

receipt_api = ReceiptApi()

api_router.add_api_route("/create-receipt", receipt_api.create_receipt, methods=["POST"])
api_router.add_api_route("/get-receipt/{receipt_id}", receipt_api.get_receipt_by_id, methods=["GET"])
api_router.add_api_route("/get-receipts", receipt_api.get_receipts, methods=["GET"])
api_router.add_api_route("/get-receipt-text/{receipt_id}", receipt_api.get_receipt_text, methods=["GET"], response_class=PlainTextResponse)
