from ..core.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    branch_id = Column(Integer, ForeignKey("branches.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    branch = relationship("Branch", back_populates="students")
    group = relationship("Group", back_populates="students")
    teacher = relationship("Teacher", back_populates="students")

    def __repr__(self):
        return f"<Student id={self.id}, email={self.email}>"