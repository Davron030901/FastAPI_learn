from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: int | None = None
    role: str | None = None
    branch_id: int | None = None