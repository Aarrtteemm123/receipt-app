from tortoise import fields
from tortoise.models import Model


class Receipt(Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="receipts")
    payment_type = fields.ForeignKeyField("models.PaymentType", related_name="receipts")
    amount = fields.FloatField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "receipts"

