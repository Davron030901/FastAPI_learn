from typing import Optional

from pydantic import BaseModel

class BranchBase(BaseModel):
    name: str
    address: str

class BranchCreate(BranchBase):
    pass

class BranchUpdate(BranchBase):
    name: Optional[str] = None
    address: Optional[str] = None

class BranchSchema(BranchBase):
    id: int

    class Config:
        orm_mode = True