from fastapi import FastAPI,Request,Form,status,Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from . database.db import engine,Base
from . models import user,interview,interview_turn
from sqlalchemy.orm import Session
from . database.db import get_db
from . auth import routes as auth_routes
from . mock_interview import routes as mock_routes


app=FastAPI()

Base.metadata.create_all(bind=engine)


templates = Jinja2Templates("app/templates")
app.mount("/static", StaticFiles(directory="app/static"))

app.include_router(auth_routes.router)
app.include_router(mock_routes.router)







