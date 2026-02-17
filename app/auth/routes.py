from fastapi import APIRouter,Request,Form,status,Depends
from fastapi.templating import Jinja2Templates  
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .. database.db import get_db
from .. models import user
from . dependencies import get_hashed,verify_password
from datetime import timedelta
from . token import create_access_token,ACCESS_TOKEN_EXPIRE_MINUTES
from .dependencies import get_current_user
from ..models.interview import Interview
from ..models.interview_evaluation import InterviewEvaluation


router=APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates("app/templates")

@router.get("/register",name="register")
def register(request:Request):
    return templates.TemplateResponse("auth.html",{"request":request})

@router.get("/login",name="login")
def root(request:Request):
    return templates.TemplateResponse("login.html",{"request":request})


@router.post("/register",name="register")
def register(name:str =Form(...),
             email:str=Form(...),
             password:str=Form(...),
             phone_no:str=Form(...),
             db:Session=Depends(get_db)
             ):
    if db.query(user.User).filter(user.User.email==email).first():
        return RedirectResponse(url="/auth/register",status_code=status.HTTP_303_SEE_OTHER)
    if db.query(user.User).filter(user.User.phone_no==phone_no).first():
        return RedirectResponse(url="/auth/register",status_code=status.HTTP_303_SEE_OTHER)
    hashed_password=get_hashed(password)
    new_user=user.User(name=name,email=email,password_hashed=hashed_password,phone_no=phone_no)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(
        data={"user_id": new_user.user_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    response = RedirectResponse("/auth/dash", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="session",
        value=access_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
    )

    return response
    

@router.post("/login", name="login_post")
def login_submit(
                email:str=Form(...),
                password:str=Form(...),
                db:Session=Depends(get_db)
                ):
    user_in_db=db.query(user.User).filter(user.User.email==email).first()
    if not user_in_db:
        return RedirectResponse(url="/auth/login",status_code=status.HTTP_303_SEE_OTHER)
    if not verify_password(password, user_in_db.password_hashed):
        return RedirectResponse(url="/auth/login",status_code=status.HTTP_303_SEE_OTHER)
    
    access_token = create_access_token(
        data={"user_id": user_in_db.user_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    response = RedirectResponse("/auth/dash", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="session",
        value=access_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
    )

    return response

@router.get("/dash",name="dashboard")
def dashboard(request:Request,current_user=Depends(get_current_user)):
    if isinstance(current_user, RedirectResponse):
        return current_user
    return templates.TemplateResponse("dash.html",{"request":request,"user":current_user})

@router.post("/logout",name="logout")
def logout():
    response = RedirectResponse("/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="session")
    return response

@router.get("/history",name="history")
def history(request:Request,
            current_user=Depends(get_current_user),
            db:Session=Depends(get_db)):
    if isinstance(current_user, RedirectResponse):
        return current_user
    interviews = (
        db.query(Interview)
        .filter(Interview.user_id == current_user.user_id)
        .order_by(Interview.created_at.desc())
        .all()
    )
    history_data = []
    for i in interviews:
        history_data.append({
            "interview_id": i.interview_id,
            "interview_type": i.interview_type,
            "mode": i.mode,
            "difficulty": i.difficulty,
            "status": i.status,
            "score": i.evaluation.score if i.evaluation else "Pending",
            "date": i.created_at.strftime("%d %b %Y")
        })

    return templates.TemplateResponse(
        "history.html",
        {"request": request, "history": history_data}
    )

@router.get("/history/{interview_id}", name="evaluation_detail")
def evaluation_detail(request: Request, interview_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if isinstance(current_user, RedirectResponse):
        return current_user

    evaluation = (
        db.query(InterviewEvaluation)
        .join(Interview)
        .filter(Interview.interview_id == interview_id, Interview.user_id == current_user.user_id)
        .first()
    )

    if not evaluation:
        return RedirectResponse(url="/auth/history", status_code=status.HTTP_303_SEE_OTHER)

    return {
        "score": evaluation.score,
        "strengths": evaluation.strengths,
        "weaknesses": evaluation.weaknesses,
        "improvements": evaluation.improvements,
        "final_verdict": evaluation.final_verdict
    }