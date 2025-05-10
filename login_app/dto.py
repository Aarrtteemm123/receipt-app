from pydantic import BaseModel


class NewUserDto(BaseModel):
    name: str
    username: str
    password: str

class LoginUserDto(BaseModel):
    username: str
    password: str