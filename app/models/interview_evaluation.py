from ..database.db import Base
from sqlalchemy import Column,Integer,String ,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime
from datetime import datetime

class InterviewEvaluation(Base):
    __tablename__="interview_evaluations"
    evaluation_id=Column(Integer,primary_key=True,index=True)
    interview_id=Column(Integer,ForeignKey("interviews.interview_id"),nullable=False)
    score=Column(Integer,nullable=False)
    strengths=Column(String,nullable=False)
    weaknesses=Column(String,nullable=False)
    improvements=Column(String,nullable=False)
    final_verdict=Column(String,nullable=False)
    created_at=Column(DateTime, default=datetime.utcnow)
    interview=relationship("Interview", back_populates="evaluation")
