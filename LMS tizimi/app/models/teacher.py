from ..core.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    branch_id = Column(Integer, ForeignKey("branches.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    branch = relationship("Branch", back_populates="teachers")
    group = relationship("Group", back_populates="teachers")
    students = relationship("Student", back_populates="teacher")

    def __repr__(self):
        return f"<Teacher id={self.id}, email={self.email}>"