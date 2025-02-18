from typing import Optional

from pydantic import BaseModel, EmailStr

class StudentBase(BaseModel):
    full_name: str
    email: EmailStr
    branch_id: int

class StudentCreate(StudentBase):
    pass

class StudentUpdate(StudentBase):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    branch_id: Optional[int] = None

class StudentSchema(StudentBase):
    id: int
    branch_id: int

    class Config:
        orm_mode = True