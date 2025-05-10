from pydantic import BaseModel


class NewUserDto(BaseModel):
    name: str
    username: str
    password: str