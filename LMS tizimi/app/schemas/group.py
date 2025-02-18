from typing import Optional

from pydantic import BaseModel

class GroupBase(BaseModel):
    name: str
    branch_id: int
    teacher_id: int # User ID sifatida

class GroupCreate(GroupBase):
    pass

class GroupUpdate(GroupBase):
    name: Optional[str] = None
    branch_id: Optional[int] = None
    teacher_id: Optional[int] = None

class GroupSchema(GroupBase):
    id: int
    branch_id: int
    teacher_id: int

    class Config:
        orm_mode = True