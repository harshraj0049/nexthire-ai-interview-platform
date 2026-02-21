from ..models.interview import Interview
from ..models.interview_turn import InterviewTurn
from ..models.interview_evaluation import InterviewEvaluation
from app.models import interview

def create_interview_in_db(db, user_id, interview_type, difficulty, mode, language):
    interview=Interview(user_id=user_id,
                        interview_type=interview_type,
                        difficulty=difficulty,
                        language=language,
                        mode=mode,status="IN_PROGRESS")
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview

def create_turn(db, interview_id, question):
    first_turn=InterviewTurn(interview_id=interview_id,
                             role="INTERVIEWER",
                             content=question)
    db.add(first_turn)
    db.commit()
    db.refresh(first_turn)
    
def create_user_turn(db,interview_id,content):
    turn=InterviewTurn(interview_id=interview_id,role="USER",content=content)
    db.add(turn)
    db.commit()
    db.refresh(turn)

def create_interviwer_turn(db,interview_id,content):
    turn=InterviewTurn(interview_id=interview_id,role="INTERVIEWER",content=content)
    db.add(turn)
    db.commit()
    db.refresh(turn)

def get_interview_for_user(db,interview_id,user_id):
    return db.query(Interview).filter(Interview.interview_id==interview_id,
                                         Interview.user_id==user_id).first()

def get_all_interview_turns(db,interview_id):
    return db.query(InterviewTurn).filter(InterviewTurn.interview_id==interview_id).order_by(InterviewTurn.created_at.asc()).all()

def get_insufficient_evaluation_in_db(db,interview_id):
     return InterviewEvaluation(
        interview_id=interview_id,
        score=0,
        strengths = "No meaningful attempt.",
        weaknesses = "Interview ended before substantial participation.",
        improvements = "Attempt full questions before ending interview.",
        final_verdict = "Insufficient attempt."
        )

def get_failed_evaluation_db(interview_id):
    return InterviewEvaluation(
                interview_id=interview_id,
                score=0,
                strengths="Evaluation failed.",
                weaknesses="AI could not process.",
                improvements="Retry later.",
                final_verdict="Incomplete evaluation."
            )

def get_evaluation_db(interview_id,evaluation):
    return InterviewEvaluation(
            interview_id=interview_id,
            score=evaluation.score,
            strengths=evaluation.strengths,
            weaknesses=evaluation.weaknesses,
            improvements=evaluation.improvements,
            final_verdict=evaluation.final_verdict,
        )

def save_evaluation_in_db(db,evaluation_db):
    db.add(evaluation_db)
    db.commit()
    db.refresh(evaluation_db)

def update_interview_status(db,interview_id,status):
    interview=db.query(Interview).filter(Interview.interview_id==interview_id).first()
    if interview:
        interview.status=status
    db.commit()
    db.refresh(interview)