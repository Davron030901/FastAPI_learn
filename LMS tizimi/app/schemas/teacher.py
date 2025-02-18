from typing import Optional

from pydantic import BaseModel

class TeacherBase(BaseModel):
    user_id: int
    branch_id: int

class TeacherCreate(TeacherBase):
    pass

class TeacherUpdate(TeacherBase):
    branch_id: Optional[int] = None

class TeacherSchema(TeacherBase):
    id: int
    user_id: int
    branch_id: int

    class Config:
        orm_mode = True