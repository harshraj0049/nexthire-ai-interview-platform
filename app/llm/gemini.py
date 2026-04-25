import logging
import os
import asyncio
from google.genai import types 
from google import genai
from dotenv import load_dotenv
from ..schemas.all_schemas import InterviewEvaluationSchema
import time

logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


MODEL_FALLBACKS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
]


"""async def call_gemini_api(prompt: str) -> str:
    logger.info("Calling Gemini API")

    try:
        start=time.perf_counter()
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=prompt
        )
        latency=time.perf_counter()-start
        logger.info(f"Received response from Gemini API with latency{latency:.3f} sec")

        if getattr(response, "error", None):
            logger.error(
                f"Gemini error: code={response.error.code}, message={response.error.message}"
            )

        return response.text

    except Exception as e:
        logger.error("Gemini API call failed", exc_info=True)
        raise"""

async def call_gemini_api(prompt: str) -> str:
    logger.info("Calling Gemini API with smart fallback")

    for model_name in MODEL_FALLBACKS:
        try:
            start = time.perf_counter()

            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model_name,
                contents=prompt,
            )

            latency = time.perf_counter() - start
            logger.info(f"{model_name} success in {latency:.3f}s")

            if getattr(response, "error", None):
                raise Exception(response.error.message)

            return response.text

        except Exception as e:
            error_msg = str(e).lower()

            if "quota" in error_msg or "rate" in error_msg or "unavailable" in error_msg:
                logger.warning(f"{model_name} exhausted → switching")
                continue
            else:
                logger.error(f"Unexpected error in {model_name}")
                raise

    raise Exception("All Gemini models failed")


"""async def evaluate_interview(prompt: str) -> InterviewEvaluationSchema:
    logger.info("Evaluating interview with Gemini API")

    try:
        start=time.perf_counter()
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": InterviewEvaluationSchema.model_json_schema(),
            },
        )
        latency=time.perf_counter()-start

        logger.info(f"Received evaluation from Gemini API with latency {latency:.3f} sec")

        if getattr(response, "error", None):
            logger.error(
                f"Gemini error: code={response.error.code}, message={response.error.message}"
            )

        return InterviewEvaluationSchema.model_validate_json(response.text)

    except Exception:
        logger.error("Interview evaluation failed", exc_info=True)
        raise"""

async def evaluate_interview(prompt: str) -> InterviewEvaluationSchema:
    logger.info("Evaluating interview using Gemma 4 31B")

    for model_name in ["gemma-4-31b-it", "gemini-2.5-flash-lite"]:
        try:
            start = time.perf_counter()

            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="high"),
                    system_instruction="""
                        You are an expert technical interviewer.

                        Evaluate the candidate based on:
                        - Technical correctness
                        - Clarity of explanation
                        - Problem-solving approach
                        - Communication

                        Be strict and realistic.

                    Return ONLY valid JSON matching the schema.
                    Do not include extra text.
                    """,
                    response_mime_type="application/json",
                    response_json_schema=InterviewEvaluationSchema.model_json_schema(),
                    temperature=0.1,
                ),
            )

            latency = time.perf_counter() - start
            logger.info(f"{model_name} eval in {latency:.3f}s")

            if getattr(response, "error", None):
                raise Exception(response.error.message)

            json_str = response.text.strip()

            # retry validation once
            for attempt in range(2):
                try:
                    return InterviewEvaluationSchema.model_validate_json(json_str)
                except Exception:
                    logger.warning(f"Validation failed attempt {attempt+1}")

            raise Exception("Invalid JSON after retry")

        except Exception as e:
            logger.warning(f"{model_name} failed: {str(e)}")
            continue

    raise Exception("All evaluation models failed")