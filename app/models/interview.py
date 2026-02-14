from ..database.db import Base
from sqlalchemy import Column,Integer,ForeignKey,String
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime
from datetime import datetime
from sqlalchemy.sql import func

class Interview(Base):
    __tablename__="interviews"
    interview_id=Column(Integer, primary_key=True, index=True)
    user_id=Column(Integer, ForeignKey("users.user_id"), nullable=False)
    interview_type=Column(String, nullable=False)
    difficulty=Column(String,nullable=False)
    mode=Column(String,nullable=False)
    language = Column(String, nullable=True)
    status=Column(String,nullable=False,default="scheduled")
    created_at=Column(DateTime(timezone=True), server_default=func.now())
    ended_at=Column(DateTime, nullable=True)
    user=relationship("User", back_populates="interviews")
    turn=relationship("InterviewTurn", back_populates="interview")
    evaluation = relationship(
        "InterviewEvaluation",
        back_populates="interview",
        uselist=False,          # IMPORTANT: one-to-one
        cascade="all, delete"
    )