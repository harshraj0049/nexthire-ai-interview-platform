from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
from .flash import flash_msg
from fastapi.responses import RedirectResponse
from fastapi import status

load_dotenv()

def get_user_id(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        return request.client.host   # anonymous users -> IP rate limit

    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        user_id = payload.get("user_id")

        if user_id:
            return f"user:{user_id}"

    except JWTError:
        pass
    return request.client.host   # fallback to IP rate limit if token is invalid

class UserRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.user=get_user_id(request)
        response=await call_next(request)
        return response
    

#set up rate limiter
limiter=Limiter(key_func=get_user_id)

#rate limit handler 
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    path = request.url.path

    if "login" in path:
        msg = "Too many login attempts"
    elif "otp" in path:
        msg = "Too many OTP attempts"
    else:
        msg = "Too many requests"

    # flash message
    flash_msg(request, f"Please slow down. {msg}", "warning")

    # send user back to previous page
    referer = request.headers.get("referer")

    return RedirectResponse(
        url=referer,
        status_code=status.HTTP_303_SEE_OTHER
    )
