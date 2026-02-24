from ..auth.token import create_access_token,ACCESS_TOKEN_EXPIRE_MINUTES
from ..repository.user import get_user_by_email,get_user_by_phone,create_user,get_user_by_id
from ..repository.interview_repo import get_user_interviews,get_evaluation_from_db
from .dependencies import get_hashed,verify_password,verify_access_token,send_password_reset_email
from ..repository.reset_session import create_password_reset_session_in_db,get_reset_session_by_token,increment_reset_attempts,reset_session_verified,reset_session_delete
from datetime import datetime,timedelta,timezone
from ..utils.otp import generate_otp
from enum import Enum
from ..repository.resume_repo import get_user_resume

#class to represent result of registration attempt
class RegisterResult:
    def __init__(self, access_token=None, error=None):
        self.access_token = access_token
        self.error = error

#service function to register user
async def register_user(db, name, email, password, phone_no):
    # duplicate check
    if get_user_by_email(db, email):
        return RegisterResult(error="Email already registered. Please log in.")

    if get_user_by_phone(db, phone_no):
        return RegisterResult(error="Phone number already registered. Please log in.")

    # hash password
    hashed = get_hashed(password)

    # create user
    user = create_user(db, name, email, hashed, phone_no)

    # create token
    token = create_access_token(
        data={"user_id": user.user_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return RegisterResult(access_token=token)

#class to represent result of login attempt
class LoginResult:
    def __init__(self, access_token=None, error=None):
        self.access_token = access_token
        self.error = error

#service function to login user
async def login_user(db, email, password):
    # fetch user
    user = get_user_by_email(db, email)

    # generic error (avoid account enumeration)
    if not user or not verify_password(password, user.password_hashed):
        return LoginResult(error="Invalid email or password")

    # create token
    token = create_access_token(
        data={"user_id": user.user_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return LoginResult(access_token=token)

#service function to get user interview history data
def get_history_for_user(db, user_id):
    interviews = get_user_interviews(db, user_id)

    history = []

    for i in interviews:
        history.append(
            {
                "interview_id": i.interview_id,
                "interview_type": i.interview_type,
                "mode": i.mode,
                "difficulty": i.difficulty,
                "status": i.status,
                "score": i.evaluation.score if i.evaluation else "Pending",
                "date": i.created_at.strftime("%d %b %Y"),
            }
        )

    return history

#service function to get interview evaluation for an interview
def get_evaluation_for_interview(db, interview_id,user_id):
    evaluation = get_evaluation_from_db(db, interview_id,user_id)
    return evaluation

#service function to create password reset session and send email
def create_password_reset_session(db,email):
    user_in_db=get_user_by_email(db,email)
    if not user_in_db:
        return None
    
    otp= generate_otp()

    hashed_otp = get_hashed(otp)

    otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)

    reset_session=create_password_reset_session_in_db(db,user_in_db.user_id,hashed_otp,otp_expiry)

    send_password_reset_email(
        to=user_in_db.email,
        subject="Password Reset OTP",
        body=f"Your OTP for password reset is: {otp}. It is valid for 5 minutes."
    )
    return reset_session

#service function to verify password reset otp
def verify_reset_otp(db, token, otp):
    reset_session = get_reset_session_by_token(db, token)
    if not reset_session:
        return "INVALID_SESSION", None

    # Too many attempts
    if reset_session.reset_attempts >= 5:
        reset_session_delete(db, reset_session.session_id)
        return "TOO_MANY_ATTEMPTS", None

    # Wrong OTP
    if not verify_password(otp, reset_session.otp):
        increment_reset_attempts(db, reset_session.session_id)
        return "INVALID_OTP", reset_session

    # Success
    reset_session_verified(db, reset_session.session_id)

    return "SUCCESS", reset_session

#class to represent result of password reset attempt
class PasswordResetStatus(str, Enum):
    UNAUTHORIZED = "unauthorized"
    SESSION_INVALID = "session_invalid"
    USER_NOT_FOUND = "user_not_found"
    SUCCESS = "success"

#service function to set new password after successful otp verification
def set_new_password(db, reset_session_id, new_password):
    if not reset_session_id:
        return PasswordResetStatus.UNAUTHORIZED, None

    reset_session = get_reset_session_by_token(db, reset_session_id)
    if not reset_session:
        return PasswordResetStatus.SESSION_INVALID, None

    if not reset_session.verified or reset_session.otp_expiry < datetime.now(timezone.utc):
        reset_session_delete(db, reset_session.session_id)
        return PasswordResetStatus.SESSION_INVALID, None

    user_in_db = get_user_by_id(db, reset_session.user_id)

    if not user_in_db:
        return PasswordResetStatus.USER_NOT_FOUND, None

    # update password
    user_in_db.password_hashed = get_hashed(new_password)

    # delete session
    reset_session_delete(db, reset_session_id)

    return PasswordResetStatus.SUCCESS, user_in_db

#class to represent result of profile fetch attempt
class ProfileStatus(str, Enum):
    NOT_FOUND = "not_found"
    SUCCESS = "success"

#service function to get user profile data
def get_user_profile(db, user_id):
    user_in_db = get_user_by_id(db, user_id)
    if not user_in_db:
        return ProfileStatus.NOT_FOUND, None

    user_resume =get_user_resume(db, user_id)

    profile_data = {
        "name": user_in_db.name,
        "email": user_in_db.email,
        "phone_no": user_in_db.phone_no,
        "resume_status": "Uploaded" if user_resume else "Not Uploaded",
    }

    return ProfileStatus.SUCCESS, profile_data


