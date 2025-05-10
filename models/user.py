import bcrypt
from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=200)
    username = fields.CharField(max_length=200, unique=True)
    password = fields.CharField(max_length=600)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"

    def __str__(self):
        return f"<User id: {self.id} username: {self.username}>"

    def set_password(self, password: str):
        salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))

