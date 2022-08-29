from enum import Enum

import strawberry.experimental.pydantic.conversion_types
from pydantic import BaseModel


@strawberry.enum
class DynamiteErrorTypes(Enum):
    INVALID_LOGIN = 1
    ENTITY_ALREADY_EXIST = 2
    NOT_IN_SCOPE = 3
    DISALLOWED_CHARACTERS = 4




class DynamiteError(Exception):
    def __init__(self, code: DynamiteErrorTypes, message: str):
        self.code = code
        self.message = message
