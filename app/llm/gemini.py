import logging
import os
import asyncio
from google import genai
from dotenv import load_dotenv
from ..schemas.all_schemas import InterviewEvaluationSchema

logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


async def call_gemini_api(prompt: str) -> str:
    logger.info("Calling Gemini API")

    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=prompt
        )

        logger.info("Received response from Gemini API")

        if getattr(response, "error", None):
            logger.error(
                f"Gemini error: code={response.error.code}, message={response.error.message}"
            )

        return response.text

    except Exception as e:
        logger.error("Gemini API call failed", exc_info=True)
        raise


async def evaluate_interview(prompt: str) -> InterviewEvaluationSchema:
    logger.info("Evaluating interview with Gemini API")

    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": InterviewEvaluationSchema.model_json_schema(),
            },
        )

        logger.info("Received evaluation from Gemini API")

        if getattr(response, "error", None):
            logger.error(
                f"Gemini error: code={response.error.code}, message={response.error.message}"
            )

        return InterviewEvaluationSchema.model_validate_json(response.text)

    except Exception:
        logger.error("Interview evaluation failed", exc_info=True)
        raise