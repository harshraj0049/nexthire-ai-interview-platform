from fastapi import Request
from sqlalchemy.orm import Session
from ..models.user_resume import UserResume


def resume_upload_in_db(user_id:str,db:Session,resume_summary:str):
    existing_resume = db.query(UserResume).filter(UserResume.user_id == user_id).first()
    if existing_resume:
        existing_resume.resume_data = resume_summary
    else:
        db.add(UserResume(user_id=user_id,resume_data=resume_summary,))
    db.commit()

def get_user_resume(db,user_id):
    resume= db.query(UserResume).filter(UserResume.user_id == user_id).first()
    return resume