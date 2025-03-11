from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, Numeric
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String)
    password = Column(String)
    is_staff = Column(Boolean, default=False)
    
    plates = relationship("AutoPlate", back_populates="created_by")
    bids = relationship("Bid", back_populates="user")

class AutoPlate(Base):
    __tablename__ = "auto_plates"
    
    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, unique=True, index=True)
    description = Column(String)
    deadline = Column(DateTime)
    starting_price = Column(Numeric(10, 2), nullable=False, default=1000)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    
    created_by = relationship("User", back_populates="plates")
    bids = relationship("Bid", back_populates="plate", cascade="all, delete-orphan")

class Bid(Base):
    __tablename__ = "bids"
    
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10, 2))
    user_id = Column(Integer, ForeignKey("users.id"))
    plate_id = Column(Integer, ForeignKey("auto_plates.id"))
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="bids")
    plate = relationship("AutoPlate", back_populates="bids")
    
    __table_args__ = (
        # Each user can have only one bid per plate
        # (Replaced later with logic in bid creation/update)
    )