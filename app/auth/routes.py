from fastapi import APIRouter,Request,Form,status,Depends
from fastapi.templating import Jinja2Templates  
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .. database.db import get_db
from .dependencies import get_current_user
import logging
from ..utils.rate_limit import limiter
from ..utils.flash import flash_msg,get_flash
from .services import register_user,login_user,get_history_for_user,get_evaluation_for_interview,create_password_reset_session,verify_reset_otp,set_new_password,PasswordResetStatus,get_user_profile,ProfileStatus
from ..repository.interview_repo import get_avg_scores,recent_3_avg_score
logger=logging.getLogger(__name__)


router=APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates("app/templates")

#api endpoint to render registration page
@router.get("/register",name="register")
def register(request:Request):
    return templates.TemplateResponse("auth.html",{"request":request,"flash": get_flash(request)})


#api endpoint to render login page
@router.get("/login",name="login")
def root(request:Request):
    return templates.TemplateResponse("login.html",{"request":request,"flash": get_flash(request)})


#register endpoint
@router.post("/register",name="register")
async def register(request:Request,
             name:str =Form(...),
             email:str=Form(...),
             password:str=Form(...),
             phone_no:str=Form(...),
             db:Session=Depends(get_db)
             ):
    result = await register_user(
        db=db,
        name=name,
        email=email,
        password=password,
        phone_no=phone_no,
    )

    if result.error:
        flash_msg(request, result.error, "error")
        logger.warning(f"Registration attempt failed for email {email}: {result.error}")
        return RedirectResponse("/auth/register", status_code=303)
    
    logger.info(f"New user registered with email {email}")
    flash_msg(request, "Registration successful!", "success")

    response = RedirectResponse("/auth/dash", status_code=303)
    response.set_cookie(
        key="access_token",
        value=result.access_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
    )
    return response


#login endpoint
@router.post("/login", name="login_post")
@limiter.limit("5/minute")
async def login_submit(request:Request,
                email:str=Form(...),
                password:str=Form(...),
                db:Session=Depends(get_db)
                ):
    result = await login_user(db, email, password)

    if result.error:
        flash_msg(request, result.error, "error")
        logger.warning(f"Login attempt failed for email {email}: {result.error}")
        return RedirectResponse("/auth/login", status_code=303)

    logger.info(f"User with email {email} logged in successfully")
    flash_msg(request, "Login successful!", "success")

    response = RedirectResponse("/auth/dash", status_code=303)
    response.set_cookie(
        key="access_token",
        value=result.access_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
    )
    return response

   
#api endpoint to render user dashboard
@router.get("/dash",name="dashboard")
def dashboard(request:Request,current_user=Depends(get_current_user)):
    if isinstance(current_user, RedirectResponse):
        return current_user
    return templates.TemplateResponse("dash.html",{"request":request,"user":current_user,"name":current_user.name,"flash": get_flash(request)})


#logout endpoint
@router.post("/logout",name="logout")
def logout(request:Request,current_user=Depends(get_current_user)):
    flash_msg(request,"You have been logged out successfully.","success")
    response = RedirectResponse("/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="session")
    logger.info(f"User with user_id {current_user.user_id} logged out")
    return response


#api endpoint to show user interview history
@router.get("/history",name="history")
def history(request:Request,
            current_user=Depends(get_current_user),
            db:Session=Depends(get_db)):
    if isinstance(current_user, RedirectResponse):
        return current_user
    history_data = get_history_for_user(
        db=db,
        user_id=current_user.user_id,
    )

    avg_score=get_avg_scores(db,current_user.user_id)
    recent_avg=recent_3_avg_score(db,current_user.user_id)

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "history": history_data,
            "avg_score": avg_score,
            "recent_avg": recent_avg,
            "flash": get_flash(request),
        },
    )


#api endpoint to show evaluation details for an interview
@router.get("/history/{interview_id}", name="evaluation_detail")
def evaluation_detail(request: Request, interview_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if isinstance(current_user, RedirectResponse):
        return current_user

    evaluation = get_evaluation_for_interview(db, interview_id,current_user.user_id)

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
    reset_session = create_password_reset_session(db, email)

    flash_msg(
        request,
        "If the email exists in our system, an OTP has been sent.",
        "info"
    )

    if not reset_session:
        logger.warning(f"Password reset requested for non-existent email {email}")
        return RedirectResponse("/auth/login", status_code=303)

    logger.info(f"Password reset session {reset_session.session_id} created for user {reset_session.user_id}")
    return RedirectResponse(
        url=f"/auth/verify_otp?token={reset_session.session_id}",
        status_code=303
    )


#api endpoint to render otp verification page
@router.get("/verify_otp",name="verify_otp")
def verify_otp_page(request:Request,token:str):
    return templates.TemplateResponse("verify_otp.html",{"request":request,"token":token,"flash": get_flash(request)})


#api endpoint to verify otp and render new password page
@router.post("/verify_otp",name="verify_otp_post")
@limiter.limit("3/minute")
def verify_otp_submit(request:Request,token:str=Form(...), otp:str=Form(...),db:Session=Depends(get_db)):
    status_result, reset_session = verify_reset_otp(db, token, otp)

    if status_result == "INVALID_SESSION":
        flash_msg(request, "OTP is invalid or expired.", "error")
        return RedirectResponse("/auth/reset_password", 303)

    if status_result == "TOO_MANY_ATTEMPTS":
        flash_msg(request, "Too many attempts. Start reset again.", "error")
        return RedirectResponse("/auth/reset_password", 303)

    if status_result == "INVALID_OTP":
        flash_msg(request, "OTP is invalid. Try again.", "error")
        return RedirectResponse(f"/auth/verify_otp?token={token}", 303)

    # SUCCESS
    flash_msg(request, "OTP verified. Set new password.", "success")

    response = RedirectResponse("/auth/new_password", 303)

    response.set_cookie(
        key="reset_session_id",
        value=str(reset_session.session_id),
        httponly=True,
        max_age=300,
        samesite="lax"
    )
    return response


#api endpoint to render new password page
@router.get("/new_password",name="new_password")
def new_password_page(request:Request):
    return templates.TemplateResponse("new_password.html",{"request":request,"flash": get_flash(request)})


#api endpoint to set new password
@router.post("/new_password",name="new_password_post")
@limiter.limit("3/minute")
def new_password_submit(request:Request, new_password:str=Form(...), db:Session=Depends(get_db)):
    reset_session_id = request.cookies.get("reset_session_id")

    status_result, user_obj = set_new_password(
        db,
        reset_session_id,
        new_password
    )

    if status_result == PasswordResetStatus.UNAUTHORIZED:
        flash_msg(request, "Unauthorized access.", "error")
        return RedirectResponse("/auth/login", 303)

    if status_result == PasswordResetStatus.SESSION_INVALID:
        flash_msg(request, "Session expired. Restart reset.", "error")
        return RedirectResponse("/auth/login", 303)

    if status_result == PasswordResetStatus.USER_NOT_FOUND:
        flash_msg(request, "User not found.", "error")
        return RedirectResponse("/auth/login", 303)

    # SUCCESS
    logger.info(f"Password reset successful for user {user_obj.user_id}")

    flash_msg(
        request,
        "Password reset successful! Login again.",
        "success"
    )

    response = RedirectResponse("/auth/login", 303)
    response.delete_cookie("reset_session_id")

    return response


#api endpoint to show user profile
@router.get("/profile")
def get_profile_info(request:Request, db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    if isinstance(current_user, RedirectResponse):
        return current_user

    status_result, profile = get_user_profile(
        db,
        current_user.user_id
    )

    if status_result == ProfileStatus.NOT_FOUND:
        return {"message": "User not found"}

    return profile
    
