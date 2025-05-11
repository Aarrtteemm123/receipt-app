from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from fastapi.responses import PlainTextResponse

from fastapi import Request, HTTPException, Query
from tortoise.expressions import Q
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
        receipt = Receipt(user=user, amount=data.payment.amount, total=total, payment_type=payment_type)

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

    @login_required
    async def get_receipt_by_id(self, request: Request, receipt_id: int) -> ReceiptResponse:
        user = request.state.user

        receipt = await Receipt.filter(id=receipt_id, user=user).prefetch_related("products", "payment_type").first()
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")

        products = [
            ProductOutput(
                name=p.name,
                price=p.price,
                quantity=p.quantity,
                total=round(p.price * p.quantity, 2)
            )
            for p in receipt.products  # related name in the model Product
        ]
        total = receipt.total
        rest = max(receipt.amount - total, 0)

        return ReceiptResponse(
            id=receipt.id,
            products=products,
            payment=PaymentOutput(
                type=receipt.payment_type.name,
                amount=receipt.amount,
            ),
            total=round(total, 2),
            rest=round(rest, 2),
            created_at=receipt.created_at
        )

    @login_required
    async def get_receipts(
            self,
            request: Request,
            date_from: Optional[datetime] = Query(None),
            date_to: Optional[datetime] = Query(None),
            min_total: Optional[float] = Query(None),
            payment_type: Optional[str] = Query(None),
            offset: int = Query(0, ge=0),
            limit: int = Query(10, le=100),
    ) -> List[ReceiptResponse]:
        user = request.state.user
        filters = Q(user=user)

        if date_from:
            filters &= Q(created_at__gte=date_from)
        if date_to:
            filters &= Q(created_at__lte=date_to)
        if min_total is not None:
            filters &= Q(total__gte=min_total)
        if payment_type:
            filters &= Q(payment_type__name=payment_type)

        receipts = await Receipt.filter(
            filters
        ).prefetch_related(
            "payment_type", "products"
        ).offset(offset).limit(limit)

        result = []
        for receipt in receipts:
            products = [
                ProductOutput(
                    name=p.name,
                    price=p.price,
                    quantity=p.quantity,
                    total=round(p.price * p.quantity, 2)
                )
                for p in receipt.products
            ]
            total_sum = receipt.total
            rest = max(receipt.amount - total_sum, 0)
            result.append(
                ReceiptResponse(
                    id=receipt.id,
                    products=products,
                    payment=PaymentOutput(
                        type=receipt.payment_type.name,
                        amount=total_sum
                    ),
                    total=round(total_sum, 2),
                    rest=rest,
                    created_at=receipt.created_at
                )
            )

        return result

    async def get_receipt_text(
            self,
            request: Request,
            receipt_id: int,
            line_width: int = Query(32, ge=20, le=100)
    ) -> str:
        receipt = await Receipt.get_or_none(id=receipt_id).prefetch_related("products", "payment_type")
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")

        def format_line(text: str, align: str = "left") -> str:
            if align == "center":
                return text.center(line_width)
            elif align == "right":
                return text.rjust(line_width)
            return text.ljust(line_width)

        def format_money(value: Decimal) -> str:
            return f"{value:,.2f}".replace(",", " ")

        lines = []
        lines.append(format_line("ФОП Джонсонюк Борис", "center"))
        lines.append("=" * line_width)

        total = Decimal("0.00")
        for p in receipt.products:
            subtotal = Decimal(p.price * p.quantity)
            total += subtotal
            lines.append(f"{p.quantity:.2f} x {format_money(p.price)}")
            lines.append(format_line(p.name, "left") + format_money(subtotal).rjust(line_width - len(p.name)))
            lines.append("-" * line_width)

        lines.append("=" * line_width)
        lines.append(format_line("СУМА" + format_money(total).rjust(line_width - 4)))
        lines.append(format_line(receipt.payment_type.name.capitalize() + format_money(total).rjust(line_width - len(receipt.payment_type.name))))
        rest = Decimal(receipt.amount) - total
        lines.append(format_line("Решта" + format_money(rest).rjust(line_width - 5)))
        lines.append("=" * line_width)
        lines.append(format_line(receipt.created_at.strftime("%d.%m.%Y %H:%M"), "center"))
        lines.append(format_line("Дякуємо за покупку!", "center"))

        return PlainTextResponse(content="\n".join(lines))
