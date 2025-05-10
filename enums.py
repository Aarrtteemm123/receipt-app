from enum import Enum


class BaseEnum(str, Enum):

    @classmethod
    def get_list(cls):
        return [item.value for item in cls]


class TokenTypeEnum(BaseEnum):
    ACCESS = "access_token"
    REFRESH = "refresh_token"

