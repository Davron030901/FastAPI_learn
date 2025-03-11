# schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# User Schemas
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str
    is_staff: Optional[bool] = False

class UserResponse(UserBase):
    id: int
    is_staff: bool

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# AutoPlate Schemas
class AutoPlateBase(BaseModel):
    plate_number: str
    description: str
    deadline: datetime
    starting_price: Decimal = Field(default=1000, gt=0)
    
    @validator('deadline')
    def ensure_future_deadline(cls, v):
        if v <= datetime.now():
            raise ValueError('Deadline must be in the future')
        return v

    @validator('starting_price')
    def validate_starting_price(cls, v):
        if v <= 0:
            raise ValueError('Starting price must be greater than 0')
        return v

class AutoPlateCreate(AutoPlateBase):
    pass

class AutoPlateUpdate(AutoPlateBase):
    is_active: bool

    class Config:
        from_attributes = True

class AutoPlateResponse(AutoPlateBase):
    id: int
    created_by_id: int
    is_active: bool

class AutoPlateWithHighestBid(AutoPlateResponse):
    highest_bid: Optional[Decimal] = None

# Bid Schemas
class BidBase(BaseModel):
    amount: Decimal = Field(..., gt=0)

class BidCreate(BidBase):
    plate_id: int

class BidUpdate(BidBase):
    pass

class BidResponse(BidBase):
    id: int
    user_id: int
    plate_id: int
    created_at: datetime

class BidWithUser(BidResponse):
    user: UserResponse

# Combined Schemas
class AutoPlateWithBids(AutoPlateResponse):
    bids: List[BidResponse] = []

class Config:
    from_attributes = True