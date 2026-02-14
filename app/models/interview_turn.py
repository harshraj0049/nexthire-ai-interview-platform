from ..database.db import Base
from sqlalchemy import Column,Integer,String ,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime
from datetime import datetime
from sqlalchemy.sql import func

class InterviewTurn(Base):
    __tablename__="interview_turns"
    turn_id=Column(Integer,primary_key=True,index=True)
    interview_id=Column(Integer,ForeignKey("interviews.interview_id"),nullable=False)
    content=Column(String,nullable=False)
    role=Column(String,nullable=False)
    created_at=Column(DateTime(timezone=True), server_default=func.now())
    interview=relationship("Interview", back_populates="turn")