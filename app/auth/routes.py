from fastapi import APIRouter,Request,Form,status,Depends
from fastapi.templating import Jinja2Templates  
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .. database.db import get_db
from .. models import user
from . dependencies import get_hashed, send_password_reset_email,verify_password
from datetime import timedelta
from . token import create_access_token,ACCESS_TOKEN_EXPIRE_MINUTES
from .dependencies import get_current_user
from ..models.interview import Interview
from ..models.interview_evaluation import InterviewEvaluation
from ..models.user_resume import UserResume
from ..models.password_reset import PasswordResetSession
import random
import datetime
import logging
from ..utils.rate_limit import limiter
from ..utils.flash import flash_msg,get_flash

logger=logging.getLogger(__name__)


router=APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates("app/templates")

@router.get("/register",name="register")
def register(request:Request):
    return templates.TemplateResponse("auth.html",{"request":request,"flash": get_flash(request)})

@router.get("/login",name="login")
def root(request:Request):
    return templates.TemplateResponse("login.html",{"request":request,"flash": get_flash(request)})


@router.post("/register",name="register")
def register(request:Request,
             name:str =Form(...),
             email:str=Form(...),
             password:str=Form(...),
             phone_no:str=Form(...),
             db:Session=Depends(get_db)
             ):
    if db.query(user.User).filter(user.User.email==email).first():
        flash_msg(request,"Email already registered. Please log in.","error")
        return RedirectResponse(url="/auth/register",status_code=status.HTTP_303_SEE_OTHER)
    if db.query(user.User).filter(user.User.phone_no==phone_no).first():
        flash_msg(request,"Phone number already registered. Please log in.","error")
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
    logger.info(f"New user registered with user id {new_user.user_id}")
    flash_msg(request,"Registration successful!.","success")
    response = RedirectResponse("/auth/dash", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
    )

    return response
    

@router.post("/login", name="login_post")
@limiter.limit("5/minute")
def login_submit(request:Request,
                email:str=Form(...),
                password:str=Form(...),
                db:Session=Depends(get_db)
                ):
    user_in_db=db.query(user.User).filter(user.User.email==email).first()
    if not user_in_db:
        flash_msg(request,"Invalid email or password","error")
        return RedirectResponse(url="/auth/login",status_code=status.HTTP_303_SEE_OTHER)
    if not verify_password(password, user_in_db.password_hashed):
        flash_msg(request,"Invalid email or password","error")
        return RedirectResponse(url="/auth/login",status_code=status.HTTP_303_SEE_OTHER)
    
    access_token = create_access_token(
        data={"user_id": user_in_db.user_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    logger.info(f"access token created for user {user_in_db.user_id}")
    logger.info(f"User {user_in_db.user_id} logged in")
    flash_msg(request,"Login successful!","success")
    response = RedirectResponse("/auth/dash", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
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
    return templates.TemplateResponse("dash.html",{"request":request,"user":current_user,"name":current_user.name,"flash": get_flash(request)})

@router.post("/logout",name="logout")
def logout(request:Request,current_user=Depends(get_current_user)):
    flash_msg(request,"You have been logged out successfully.","success")
    response = RedirectResponse("/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="session")
    logger.info(f"User with user_id {current_user.user_id} logged out")
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
        {"request": request, "history": history_data, "flash": get_flash(request)}
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


#reset password routes
@router.get("/reset_password",name="reset_password")
def reset_password_page(request:Request):
    return templates.TemplateResponse("reset_password.html",{"request":request,"flash": get_flash(request)})


#get user email and new password ->send an unique otp to the email
@router.post("/reset_password",name="reset_password_post")
@limiter.limit("3/minute")
def reset_password_submit(request:Request,email:str=Form(...),
                          db:Session=Depends(get_db)):
    user_in_db=db.query(user.User).filter(user.User.email==email).first()
    if not user_in_db:
        flash_msg(request,"If the email exists in our system, an OTP has been sent.","info")
    
    #generate a random and unique 6 digit OTP
    otp=str(random.randint(100000,999999))
    hashed_otp=get_hashed(otp)

    #create a password reset session in the database
    otp_expiry=datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    reset_session=PasswordResetSession(user_id=user_in_db.user_id,otp=hashed_otp,otp_expiry=otp_expiry,verified=False)
    db.add(reset_session)
    db.commit()
    db.refresh(reset_session)

    #send this generated otp to the user's email using an email service
    send_password_reset_email(
        to=user_in_db.email,
        subject="Password Reset OTP",
        body=f"Your OTP for password reset is: {otp}. It is valid for 5 minutes."
    )
    flash_msg(request,"If the email exists in our system, an OTP has been sent.","info")
    response = RedirectResponse(url=f"/auth/verify_otp?token={reset_session.session_id}",status_code=status.HTTP_303_SEE_OTHER)
    return response

@router.get("/verify_otp",name="verify_otp")
def verify_otp_page(request:Request,token:str):
    return templates.TemplateResponse("verify_otp.html",{"request":request,"token":token,"flash": get_flash(request)})

@router.post("/verify_otp",name="verify_otp_post")
@limiter.limit("3/minute")
def verify_otp_submit(request:Request,token:str=Form(...), otp:str=Form(...),db:Session=Depends(get_db)):
    reset_session=db.query(PasswordResetSession).filter(PasswordResetSession.session_id == token, PasswordResetSession.otp_expiry > datetime.datetime.utcnow(), PasswordResetSession.verified == False).first()
    if not reset_session:
        flash_msg(request,"OTP is invalid or has expired.","error")
        response = RedirectResponse(url="/auth/reset_password",status_code=status.HTTP_303_SEE_OTHER)
        return response
    
    if reset_session.reset_attempts >= 5:
        db.delete(reset_session)
        db.commit()
        flash_msg(request,"Too many failed attempts. Please initiate the password reset process again.","error")
        logger.warning(f"Password reset session {reset_session.session_id} for user {reset_session.user_id} deleted due to too many failed OTP attempts")
        response = RedirectResponse(url="/auth/reset_password",status_code=status.HTTP_303_SEE_OTHER)
        return response
    
    if not verify_password(otp, reset_session.otp):
        reset_session.reset_attempts += 1
        db.commit()
        logger.warning(f"Failed OTP verification attempt {reset_session.reset_attempts} for user {reset_session.user_id}")
        flash_msg(request,"OTP is invalid. Please try again.","error")
        return RedirectResponse(url=f"/auth/verify_otp?token={token}", status_code=303)
    
    reset_session.verified = True
    db.commit()
    logger.info(f"OTP verified for user {reset_session.user_id}")
    flash_msg(request,"OTP verified successfully! Please set your new password.","success")
    response = RedirectResponse(url="/auth/new_password",status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="reset_session_id", value=str(reset_session.session_id), httponly=True, max_age=300, samesite="lax")
    return response

@router.get("/new_password",name="new_password")
def new_password_page(request:Request):
    return templates.TemplateResponse("new_password.html",{"request":request,"flash": get_flash(request)})

@router.post("/new_password",name="new_password_post")
@limiter.limit("3/minute")
def new_password_submit(request:Request, new_password:str=Form(...), db:Session=Depends(get_db)):
    reset_session_id = request.cookies.get("reset_session_id")
    if not reset_session_id:
        flash_msg(request,"Unauthorized access.","error")
        response = RedirectResponse(url="/auth/login",status_code=status.HTTP_303_SEE_OTHER)
        return response
    
    reset_session = db.query(PasswordResetSession).filter(PasswordResetSession.session_id == reset_session_id, PasswordResetSession.verified == True,
                                                          PasswordResetSession.otp_expiry > datetime.datetime.utcnow()).first()
    if not reset_session:
        logger.warning(f"Unauthorized access attempt to new password page with reset_session_id {reset_session_id}")
        flash_msg(request,"Unauthorized access or session expired.","error")
        response = RedirectResponse(url="/auth/login",status_code=status.HTTP_303_SEE_OTHER)
        return response
    
    user_in_db = db.query(user.User).filter(user.User.user_id == reset_session.user_id).first()
    if not user_in_db:
        flash_msg(request,"User not found.","error")
        response = RedirectResponse(url="/auth/login",status_code=status.HTTP_303_SEE_OTHER)
        return response
    
    user_in_db.password_hashed = get_hashed(new_password)
    db.delete(reset_session)
    db.commit()
    logger.info(f"Password reset successful for user {user_in_db.user_id}")
    flash_msg(request,"Password reset successful! Please log in with your new password.","success")
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="reset_session_id")
    return response

@router.get("/profile")
def get_profile_info(request:Request, db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    if isinstance(current_user, RedirectResponse):
        return current_user
    
    user_id = current_user.user_id

    user_in_db = db.query(user.User).filter(user.User.user_id == user_id).first()
    if not user_in_db:
        return {"message": "User not found"}
    
    user_resume = db.query(UserResume).filter(UserResume.user_id == user_id).first()
    if user_resume:
        resume_status = "Uploaded"
    else:
        resume_status = "Not Uploaded"
    
    return {
        "name": user_in_db.name,
        "email": user_in_db.email,
        "phone_no": user_in_db.phone_no,
        "resume_status": resume_status
    }
    
