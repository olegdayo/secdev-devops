from typing import Optional

from pydantic import BaseModel, constr

Username = constr(
    strip_whitespace=True,
    min_length=3,
    max_length=48,
    pattern=r"^[a-zA-Z0-9_.-]+$",
)
Password = constr(min_length=3, max_length=128)


class LoginRequest(BaseModel):
    username: Username
    password: Password


class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
