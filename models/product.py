from tortoise import fields
from tortoise.models import Model


class Product(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=200)
    price = fields.FloatField(default=0)
    quantity = fields.IntField(default=0)
    receipt = fields.ForeignKeyField("models.Receipt", related_name="products")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "products"

