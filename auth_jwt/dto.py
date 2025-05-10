from pydantic import BaseModel


class TokenDataDto(BaseModel):
    user_id: int
