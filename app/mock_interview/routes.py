from fastapi import APIRouter,Request,status,Depends,Form,UploadFile,File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .. database.db import get_db
from .. auth.dependencies import get_current_user_api
from .. schemas.all_schemas import InterviewRespond,CodeSubmitSchema
import logging
from ..utils.rate_limit import limiter
from ..utils.flash import flash_msg,get_flash
from .services import process_resume_upload,process_interview_start,process_response_to_interviwer,process_get_next_response,process_check_code,process_end_interview,get_interview_for_ui

logger=logging.getLogger(__name__)


router=APIRouter(prefix="/mock_interview", tags=["mock_interview"])

templates = Jinja2Templates("app/templates")

#resume upload route 
@router.post("/upload_resume",name="upload_resume")
@limiter.limit("3/minute")
async def upload_resume(request: Request,
                  file:UploadFile=File(...),
                  db:Session=Depends(get_db),
                  current_user=Depends(get_current_user_api)):
    if file.content_type != "application/pdf":
        flash_msg(request, "Only PDF allowed", "error")
        return RedirectResponse("/auth/dash", status_code=303)

    pdf_bytes = await file.read()

    if not pdf_bytes:
        flash_msg(request, "Empty file", "error")
        return RedirectResponse("/auth/dash", status_code=303)
    
    await process_resume_upload(request, pdf_bytes, db, current_user)

    logger.info(f"User {current_user.user_id} uploaded resume")
    flash_msg(request, "Resume uploaded and processed successfully!", "success")
    return RedirectResponse(url="/auth/dash", status_code=status.HTTP_303_SEE_OTHER)
    
    

#api endpoint to start a mock interview
@router.post("/start", name="start_mock_interview")
@limiter.limit("2/minute")
async def start_mock_interview(request: Request,
                        interview_type: str = Form(...),
                        difficulty: str = Form(...),
                        mode: str = Form(...),
                        language: str | None = Form(None),
                        db:Session =Depends(get_db),current_user=Depends(get_current_user_api)):
    
    interview_id = await process_interview_start(db,current_user.user_id,interview_type,difficulty,mode,language)
    flash_msg(request,"Mock interview started!","success")
    return RedirectResponse(
    url=f"/mock_interview/interview/{interview_id}",
    status_code=status.HTTP_303_SEE_OTHER,
)


#api endpoint for response from interview ui
@router.post("/{interview_id}/response",status_code=status.HTTP_201_CREATED)
async def respond_to_interview(interview_id:int,
                         payload:InterviewRespond,
                         db:Session=Depends(get_db),
                         current_user=Depends(get_current_user_api)):
    await process_response_to_interviwer(db,interview_id,current_user.user_id,payload.content)
    logger.info(f"Received response for interview {interview_id} from user {current_user.user_id}")
    return {"message": "Response recorded"}


#api endpoint to get next interviewer message
@router.post("/{interview_id}/next",status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def get_next_response(request: Request,
                      interview_id:int,
                      db:Session=Depends(get_db),
                      current_user=Depends(get_current_user_api)):
    
    next_message=await process_get_next_response(db,interview_id,current_user.user_id)
    logger.info(f"Generated next interviewer message for interview {interview_id} and user {current_user.user_id}")
    return {
        "role": "INTERVIEWER",
        "content": next_message,
    }


#api endpoint for code check and followup question
@router.post("/{interview_id}/check")
@limiter.limit("5/minute")
async def check_code(
    request: Request,
    interview_id: int,
    payload: CodeSubmitSchema,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_api)
    ):
    next_message=await process_check_code(db,interview_id,current_user.user_id,payload.code)
    logger.info(f"Checked code and generated follow-up for interview {interview_id} and user {current_user.user_id}")

    return {
        "role": "INTERVIEWER",
        "content": next_message,
    }


#api endpoint to end interview and generate evaluation
@router.post('/{interview_id}/end',status_code=status.HTTP_200_OK,name="end_interview")
async def end_interview(request:Request,
                  interview_id: int,
                  db:Session=Depends(get_db),
                  current_user=Depends(get_current_user_api)):
    evaluation_db=await process_end_interview(db,interview_id,current_user.user_id)

    logger.info(f"Ended interview {interview_id} for user {current_user.user_id}")
    flash_msg(request,"Interview ended! Evaluation generated.","success")
    return {
        "score": evaluation_db.score,
        "strengths": evaluation_db.strengths,
        "weaknesses": evaluation_db.weaknesses,
        "improvements": evaluation_db.improvements,
        "final_verdict": evaluation_db.final_verdict,
    }


#api endpoint to render interview ui
@router.get("/interview/{interview_id}")
def interview_ui(
    request: Request,
    interview_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_api)
    ):
    interview = get_interview_for_ui(db,interview_id,current_user.user_id)
    return templates.TemplateResponse(
        "envr.html",
        {
            "request": request,
            "interview": interview,
            "interview_id": interview_id,
            "flash": get_flash(request)
        }
    )

    
    