from ..core.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    users = relationship("User", back_populates="branch")
    groups = relationship("Group", back_populates="branch")
    teachers = relationship("Teacher", back_populates="branch")
    students = relationship("Student", back_populates="branch")

    def __repr__(self):
        return f"<Branch id={self.id}, name={self.name}>"