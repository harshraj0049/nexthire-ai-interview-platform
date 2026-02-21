import logging
from .flash import flash_msg
from fastapi import Request

logger = logging.getLogger(__name__)

async def safe_llm(request:Request,call,flash_text=None,fallback=None):
    try:
        return await call()

    except Exception:
        logger.exception("LLM failure")
        if flash_text:
            flash_msg(request,flash_text,"error")
        return fallback
