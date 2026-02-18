from ..database.db import Base
from sqlalchemy import Column, ForeignKey,Integer,String,Boolean
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid


class PasswordResetSession(Base):
    __tablename__="password_reset_sessions"
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id=Column(Integer,ForeignKey("users.user_id"), nullable=False)
    otp=Column(String,nullable=False)
    otp_expiry=Column(DateTime(timezone=True), nullable=False)
    reset_attempts=Column(Integer, default=0)
    created_at=Column(DateTime(timezone=True), server_default=func.now())
    verified=Column(Boolean, default=False)
    user=relationship("User", back_populates="password_reset_sessions")