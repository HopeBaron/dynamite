from pydantic import BaseModel


class DynamiteError(BaseModel):
    message: str
    code: int
