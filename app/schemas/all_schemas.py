from pydantic import BaseModel
from typing import Optional 
from datetime import datetime

class InterviewCreate(BaseModel):
    interview_type: str
    difficulty: str
    mode: str
    language: Optional[str]= None

class InterviewResponse(BaseModel):
    interview_id: int
    interview_type: str
    difficulty: str
    mode: str
    status: str
    created_at: datetime
    ended_at: Optional[datetime]= None

    class Config:
        orm_mode = True
        from_attributes = True

class InterviewRespond(BaseModel):
    content: str

class InterviewTurnCreate(BaseModel):
    question: str
    user_answer: Optional[str]= None
    code: Optional[str]= None
    language: Optional[str]= None

class InterviewTurnResponse(BaseModel):
    turn_id: int
    interview_id: int
    question: str
    user_answer: Optional[str]= None
    code: Optional[str]= None

    class Config:
        orm_mode = True
        from_attributes = True

class CodeSubmitSchema(BaseModel):
    code: str

