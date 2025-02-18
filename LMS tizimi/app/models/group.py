from ..core.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    branch = relationship("Branch", back_populates="groups")
    users = relationship("User", back_populates="group")
    teachers = relationship("Teacher", back_populates="group")
    students = relationship("Student", back_populates="group")


    def __repr__(self):
        return f"<Group id={self.id}, name={self.name}>"