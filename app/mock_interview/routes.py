from fastapi import APIRouter,Request,status,Depends,HTTPException,Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .. database.db import get_db
from .. auth.dependencies import get_current_user, get_current_user_api
from .. schemas.all_schemas import InterviewCreate,InterviewRespond,CodeSubmitSchema
from . services import generate_first_question,build_interview_prompt,build_evaluation_prompt
from .. models.interview import Interview
from .. models.interview_turn import InterviewTurn
from .. models.interview_evaluation import InterviewEvaluation 
from .. llm.interviewer import build_conversation,get_next_interviewer_message


router=APIRouter(prefix="/mock_interview", tags=["mock_interview"])

templates = Jinja2Templates("app/templates")

#api endpoint to start a mock interview
@router.post("/start", name="start_mock_interview")
def start_mock_interview(interview_type: str = Form(...),
                        difficulty: str = Form(...),
                        mode: str = Form(...),
                        language: str | None = Form(None),
                        db:Session =Depends(get_db),current_user=Depends(get_current_user_api)):
    
    interview=Interview(user_id=current_user.user_id,
                        interview_type=interview_type,
                        difficulty=difficulty,
                        language=language,
                        mode=mode,status="IN_PROGRESS")
    db.add(interview)
    db.commit()
    db.refresh(interview)
    #generate first question 
    question=generate_first_question(interview_type,difficulty,mode)

    first_turn=InterviewTurn(interview_id=interview.interview_id,
                             role="INTERVIEWER",
                             content=question)
    db.add(first_turn)
    db.commit()
    db.refresh(first_turn)

    return RedirectResponse(
    url=f"/mock_interview/interview/{interview.interview_id}",
    status_code=status.HTTP_303_SEE_OTHER,
)

#api endpoint for response from interview ui
@router.post("/{interview_id}/response",status_code=status.HTTP_201_CREATED)
def respond_to_interview(interview_id:int,
                         payload:InterviewRespond,
                         db:Session=Depends(get_db),
                         current_user=Depends(get_current_user_api)):
    interview=db.query(Interview).filter(Interview.interview_id==interview_id,
                                         Interview.user_id==current_user.user_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Interview not found")
    if interview.status!="IN_PROGRESS":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Interview not active")
    turn=InterviewTurn(interview_id=interview_id,role="USER",content=payload.content)
    db.add(turn)
    db.commit()
    db.refresh(turn)
    return {"message":"Response recorded"}


#api endpoint to get next interviewer message
@router.post("/{interview_id}/next",status_code=status.HTTP_201_CREATED)
def get_next_response(interview_id:int,
                      db:Session=Depends(get_db),
                      current_user=Depends(get_current_user_api)):
    
    interview=db.query(Interview).filter(Interview.interview_id==interview_id,
                                         Interview.user_id==current_user.user_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Interview not found")
    if interview.status!="IN_PROGRESS":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Interview not active")
    
    turns=db.query(InterviewTurn).filter(InterviewTurn.interview_id==interview_id).order_by(InterviewTurn.created_at.asc()).all()

    if not turns:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="interview has no conversation yet")
    
    conversation=build_conversation(turns)

    prompt=build_interview_prompt(interview,conversation)

    next_message=get_next_interviewer_message(prompt)

    turn=InterviewTurn(interview_id=interview_id,role="INTERVIEWER",content=next_message)
    db.add(turn)
    db.commit()
    db.refresh(turn)

    return {
        "role": "INTERVIEWER",
        "content": next_message,
    }

#api for code check and followup question
@router.post("/{interview_id}/check")
def check_code(
    interview_id: int,
    payload: CodeSubmitSchema,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_api)
):
    interview=db.query(Interview).filter(Interview.interview_id==interview_id,
                                         Interview.user_id==current_user.user_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Interview not found")
    if interview.status!="IN_PROGRESS":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Interview not active")

    turn = InterviewTurn(interview_id=interview_id,role="USER",content=payload.code)
    db.add(turn)
    db.commit()
    db.refresh(turn)

    turns=db.query(InterviewTurn).filter(InterviewTurn.interview_id==interview_id).order_by(InterviewTurn.created_at.asc()).all()

    if not turns:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="interview has no conversation yet")

    conversation = build_conversation(turns)

    llm_reply = get_next_interviewer_message(conversation)

    turn = InterviewTurn(interview_id=interview_id, role="INTERVIEWER", content=llm_reply)
    db.add(turn)
    db.commit()
    db.refresh(turn)

    return {
        "role": "INTERVIEWER",
        "content": llm_reply,
    }

@router.post('/{interview_id}/end',status_code=status.HTTP_200_OK)
def end_interview(interview_id:int,
                  db:Session=Depends(get_db),
                  current_user=Depends(get_current_user_api)):
    interview=db.query(Interview).filter(Interview.interview_id==interview_id,
                                         Interview.user_id==current_user.user_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Interview not found")
    interview.status="COMPLETED"
    db.commit()

    turns=db.query(InterviewTurn).filter(InterviewTurn.interview_id==interview_id).order_by(InterviewTurn.created_at.asc()).all()
    conversation=build_conversation(turns)
    evaluation_promt=build_evaluation_prompt(interview,conversation)

    evaluation=get_next_interviewer_message(evaluation_promt)
    return {"evaluation":evaluation}


#api endpoint to render interview ui
@router.get("/interview/{interview_id}")
def interview_ui(
    interview_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_api)
):
    interview = db.query(Interview).filter(
        Interview.interview_id == interview_id,
        Interview.user_id == current_user.user_id
    ).first()

    if not interview:
        raise HTTPException(status_code=404)

    return templates.TemplateResponse(
        "envr.html",
        {
            "request": request,
            "interview": interview,
            "interview_id": interview_id
        }
    )

    
    