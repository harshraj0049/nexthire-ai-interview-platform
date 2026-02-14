from ..database.db import Base
from sqlalchemy import Column,Integer,String
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime
from datetime import datetime
from sqlalchemy.sql import func

class User(Base):
    __tablename__="users"
    user_id=Column(Integer,primary_key=True,index=True)
    name=Column(String,nullable=False)
    email=Column(String,unique=True,index=True,nullable=False)
    password_hashed=Column(String,nullable=False)
    phone_no = Column(String, unique=True, nullable=True)
    created_at=Column(DateTime(timezone=True), server_default=func.now())
    interviews=relationship("Interview", back_populates="user")
    resume = relationship("UserResume", back_populates="user", uselist=False)
    


