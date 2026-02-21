from fastapi import Request,HTTPException,status
from sqlalchemy.orm import Session
from ..llm.interviewer import get_next_interviewer_message,build_conversation,build_conversation_for_eval,get_evaluation_interview
from ..llm.resume_summary import summarize_resume_with_gemini
from ..utils.ai_guard import safe_llm
import logging
from ..repository.resume_repo import resume_upload_in_db,get_user_resume
from ..repository.interview_repo import create_interview_in_db,create_turn,create_user_turn,get_interview_for_user,get_all_interview_turns,create_interviwer_turn,get_insufficient_evaluation_in_db,get_failed_evaluation_db,get_evaluation_db,save_evaluation_in_db,update_interview_status
from ..utils.prompts import build_interview_prompt,build_evaluation_prompt,get_code_evaluation_prompt

logger=logging.getLogger(__name__)

#service funtion to generate first question
def generate_first_question(interview_type: str, difficulty: str, mode: str, resume_summary: str = None) -> str:
    if resume_summary:
        return f"Tell me about yourself and your experience with {interview_type} based on your resume."
    return f"Tell me about yourself and your experience with {interview_type}."

#service function to process user resume upload
async def process_resume_upload(request:Request,pdf_bytes:bytes,db:Session,current_user):
    summary = await safe_llm(request,
                             lambda: summarize_resume_with_gemini(file_bytes=pdf_bytes,mime_type="application/pdf"),
                             flash_text="Resume processing failed",
                             fallback=None)
    if summary:
        resume_upload_in_db(current_user.user_id,db,summary)

#service function to start interview
async def process_interview_start(db,
        user_id,
        interview_type,
        difficulty,
        mode,
        language):
    #create interview record in db
    interview=create_interview_in_db(db,user_id,interview_type,difficulty,mode,language)

    #fetch user resume summary from db
    resume = get_user_resume(db, user_id)

    #generate first question
    if resume:
        question =  generate_first_question(
            interview_type,
            difficulty,
            mode,
            resume.resume_data,
        )
    else:
        question =  generate_first_question(
            interview_type,
            difficulty,
            mode,
        )
    
    #create first turn
    create_turn(db, interview.interview_id, question)

    logger.info(f"Started interview {interview.interview_id} for user {user_id}")
    return interview.interview_id

#service function to process user response to interviewer
async def process_response_to_interviwer(db,interview_id,user_id,content):
    #get interview and validate
    interview=get_interview_for_user(db,interview_id,user_id)
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Interview not found")
    if interview.status!="IN_PROGRESS":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Interview not active")
    
    #save user turn
    create_user_turn(db,interview_id,content)

#service function to get next interviewer message
async def process_get_next_response(db,interview_id,user_id):
    #get interview and validate
    interview=get_interview_for_user(db,interview_id,user_id)
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Interview not found")
    if interview.status!="IN_PROGRESS":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Interview not active")
    
    #get interview turns from db
    turns=get_all_interview_turns(db,interview_id)

    #build conversation 
    conversation=build_conversation(turns)

    #get resume summary from db
    resume_summary = get_user_resume(db, user_id)

    #build prompt for llm
    if resume_summary:
        prompt=build_interview_prompt(interview,conversation,resume_summary)
    else:
        prompt=build_interview_prompt(interview,conversation)

    #get next interviewer message from llm
    next_message=await safe_llm(None,
                                lambda: get_next_interviewer_message(prompt),
                                flash_text="Sorry,AI is busy. Please try again later.",
                                fallback="Sorry, I am having trouble generating the next question.")
    
    #save interviewer turn in db
    create_interviwer_turn(db, interview_id, next_message)
    return next_message

#service function to process code check and followup question
async def process_check_code(db,interview_id,user_id,code):
    #getinterview and validate
    interview=get_interview_for_user(db,interview_id,user_id)
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Interview not found")
    if interview.status!="IN_PROGRESS":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Interview not active")
    
    #save user turn(code submission)
    create_user_turn(db,interview_id,code)

    #get interview turns from db
    turns=get_all_interview_turns(db,interview_id)
    if not turns:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="interview has no conversation yet")
    
    #build conversation
    conversation=build_conversation(turns)

    #build prompt for llm to evaluate code
    prompt=get_code_evaluation_prompt(conversation)

    #get code feedback message from llm
    next_message=await safe_llm(None,
                                lambda: get_next_interviewer_message(prompt),
                                flash_text="Sorry,AI is busy. Please try again later.",
                                fallback="Sorry, I am having trouble generating the next question.")
    
    #save interviewer turn in db
    create_interviwer_turn(db, interview_id, next_message)

    return next_message

#service function to end interview and generate evaluation
async def process_end_interview(db,interview_id,user_id):
    #getinterview and validate
    interview=get_interview_for_user(db,interview_id,user_id)
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Interview not found")
    if interview.status!="IN_PROGRESS":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Interview not active")
    
    #get interview turns from db
    turns=get_all_interview_turns(db,interview_id)

    #build conversation for evaluation
    conversation=build_conversation_for_eval(turns)
    if conversation is None:
        #not enough conversation to evaluate
        evaluation_db=get_insufficient_evaluation_in_db(db,interview_id)
    else:
        #build prompt for llm evaluation
        prompt=build_evaluation_prompt(interview,conversation)

        #get evalaution from llm
        try:
            evaluation = await get_evaluation_interview(prompt)
        except Exception:
            logger.exception("evaluation failed")
            evaluation_db= get_failed_evaluation_db(interview_id)
        
        evaluation_db=get_evaluation_db(interview_id,evaluation)

    #save evaluation in db
    save_evaluation_in_db(db,evaluation_db)

    #update interview status to completed
    update_interview_status(db,interview_id,"COMPLETED")
    return evaluation_db

#service function to get interview details for ui
def get_interview_for_ui(db,interview_id,user_id):
    interview = get_interview_for_user(db,interview_id,user_id)

    if not interview:
        raise HTTPException(status_code=404)
    
    return interview


    