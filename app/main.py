import os
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from . database.db import engine,Base
from . auth import routes as auth_routes
from . mock_interview import routes as mock_routes
import logging
from dotenv import load_dotenv
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from .utils.rate_limit import UserRateLimitMiddleware,limiter,rate_limit_handler
from starlette.middleware.sessions import SessionMiddleware

app=FastAPI()

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s -%(name)s -%(levelname)s -%(message)s')

#rate limiter setup
app.state.limiter=limiter
app.add_exception_handler(RateLimitExceeded,rate_limit_handler)
#session middleware used for flash messages
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

app.add_middleware(UserRateLimitMiddleware)
app.add_middleware(SlowAPIMiddleware)

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates("app/templates")
app.mount("/static", StaticFiles(directory="app/static"))

app.include_router(auth_routes.router)
app.include_router(mock_routes.router)







