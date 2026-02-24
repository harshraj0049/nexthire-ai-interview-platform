import app.models
from app.database.db import SessionLocal
from datetime import datetime,timedelta,timezone
from app.models.interview_turn import InterviewTurn

def cleanup():
    db=SessionLocal()
    try:
        cutoff=datetime.now(timezone.utc)-timedelta(days=5)
        deleted=db.query(InterviewTurn).filter(InterviewTurn.created_at<cutoff).delete(synchronize_session=False)
        db.commit()
        print(deleted)
    except Exception as e:
        db.rollback()
        print(f"[CLEANUP ERROR] {e}")
    finally:
        db.close()

if __name__=="__main__":
    cleanup()