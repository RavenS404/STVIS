from pydantic import BaseModel

from app.schemas.common import ORMModel
from common.constants.enums import UserRole


class UserRead(ORMModel):
    id: str
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    last_login_at: str | None = None


class UserCreate(BaseModel):
    username: str
    full_name: str
    role: UserRole
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    password: str | None = None
    is_active: bool | None = None
