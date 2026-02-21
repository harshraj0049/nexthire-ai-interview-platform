from fastapi import Depends, Request,status, HTTPException
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .. database.db import get_db
from .. models.user import User
from . token import SECRET_KEY, ALGORITHM, verify_access_token
import os
from dotenv import load_dotenv

load_dotenv()

#mail service imports 
import smtplib
from email.message import EmailMessage

pwd_ctx = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
def get_hashed(password:str):
    return pwd_ctx.hash(password)

def verify_password(plain_password,hashed_password):
    return pwd_ctx.verify(plain_password,hashed_password)

def get_current_user(request: Request,db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/auth/login?error=not_logged_in",status_code=status.HTTP_303_SEE_OTHER)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise JWTError()
    except JWTError:
        return RedirectResponse("/auth/login?error=not_logged_in",status_code=status.HTTP_303_SEE_OTHER)
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return RedirectResponse("/auth/login?error=not_logged_in",status_code=status.HTTP_303_SEE_OTHER)
    return user

def get_current_user_api(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    payload = verify_access_token(token)
    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user

def send_password_reset_email(to:str, subject:str, body:str):
    email=EmailMessage()
    email["To"] = to
    email["Subject"] = subject
    email["From"] = "noreply@NextHire.AI"
    email.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("SMTP_EMAIL"), os.getenv("SMTP_APP_PASSWORD"))
        smtp.send_message(email)