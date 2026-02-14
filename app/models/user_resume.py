from ..database.db import Base
from sqlalchemy import Column,Integer,ForeignKey,JSON
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func


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
    resume_data = Column(JSONB, nullable=False)

    updated_at = Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now())

    user = relationship("User", back_populates="resume")