from pydantic import BaseModel, condecimal, constr, conlist
from typing import List, Literal
from datetime import datetime

from enums import PaymentTypeEnum


class ProductInput(BaseModel):
    name: constr(strip_whitespace=True, max_length=200)
    price: condecimal(gt=0, max_digits=10, decimal_places=2)
    quantity: condecimal(gt=0, max_digits=10, decimal_places=3)


class PaymentInput(BaseModel):
    type: Literal[
        PaymentTypeEnum.CREDIT_CART,
        PaymentTypeEnum.CASH
    ]
    amount: condecimal(gt=0, max_digits=10, decimal_places=2)


class ReceiptRequest(BaseModel):
    products: conlist(ProductInput, max_length=10000)
    payment: PaymentInput


class ProductOutput(ProductInput):
    total: condecimal(gt=0, max_digits=12, decimal_places=2)


class PaymentOutput(PaymentInput):
    pass


class ReceiptResponse(BaseModel):
    id: int
    products: List[ProductOutput]
    payment: PaymentOutput
    total: condecimal(gt=0, max_digits=12, decimal_places=2)
    rest: condecimal(ge=0, max_digits=10, decimal_places=2)
    created_at: datetime
