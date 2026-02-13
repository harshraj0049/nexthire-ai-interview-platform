from ..database.db import Base
from sqlalchemy import Column,Integer,String ,ForeignKey,JSON
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime
from datetime import datetime


class UserResume(Base):
    __tablename__ = "user_resumes"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    # Structured resume summary (LLM output)
    resume_data = Column(JSON, nullable=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="resume")