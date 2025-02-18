from ..core.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role_id = Column(Integer, ForeignKey("roles.id"))
    branch_id = Column(Integer, ForeignKey("branches.id")) # Yangi qo'shildi
    group_id = Column(Integer, ForeignKey("groups.id"))  # Yangi qo'shildi
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = relationship("Role", back_populates="users")
    branch = relationship("Branch", back_populates="users") # Yangi qo'shildi
    group = relationship("Group", back_populates="users")    # Yangi qo'shildi


    def __repr__(self):
        return f"<User id={self.id}, email={self.email}>"