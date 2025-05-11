from tortoise import fields
from tortoise.models import Model


class PaymentType(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=200)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "payment_types"

