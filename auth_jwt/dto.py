from pydantic import BaseModel

class TokenDto(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenDataDto(BaseModel):
    user_id: int
