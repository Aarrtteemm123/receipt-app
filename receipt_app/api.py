from fastapi import Request, HTTPException
from tortoise.transactions import in_transaction

from auth_jwt.decorators import login_required
from models import Receipt, PaymentType, Product
from receipt_app.dto import ReceiptResponse, ReceiptRequest, ProductOutput, PaymentOutput


class ReceiptApi:

    @login_required
    async def create_receipt(self, request: Request, data: ReceiptRequest) -> ReceiptResponse:
        user = request.state.user
        total = sum(p.price * p.quantity for p in data.products)
        rest = max(data.payment.amount - total, 0)

        if data.payment.amount < total:
            raise HTTPException(status_code=400, detail="Insufficient payment amount")

        products_with_total = [
            ProductOutput(**p.model_dump(), total=round(p.price * p.quantity, 2))
            for p in data.products
        ]

        payment_type = await PaymentType.get(name=data.payment.type)
        receipt = Receipt(user=user, payment_type=payment_type)

        async with in_transaction() as connection:
            await receipt.save(using_db=connection)
            products = [
                Product(
                    receipt=receipt,
                    name=product.name,
                    price=product.price,
                    quantity=product.quantity,
                )
                for product in data.products
            ]
            await Product.bulk_create(products, batch_size=100, using_db=connection)

        return ReceiptResponse(
            id=receipt.id,
            products=products_with_total,
            payment=PaymentOutput(**data.payment.model_dump()),
            total=round(total, 2),
            rest=round(rest, 2),
            created_at=receipt.created_at,
        )
