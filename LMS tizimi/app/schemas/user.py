from typing import Optional

from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    branch_id: Optional[int] = None # SuperAdmin uchun null bo'lishi mumkin
    role_id: Optional[int] = 3 # Standart role - Teacher

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    branch_id: Optional[int] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None

class UserSchema(UserBase):
    id: int
    is_active: bool
    role: "RoleSchema" # Forward reference uchun qo'shtirnoq

    class Config:
        orm_mode = True

from .role import RoleSchema # Circular import muammosini hal qilish uchun pastda import