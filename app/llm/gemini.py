from google import genai
import os
from dotenv import load_dotenv
from .. schemas.all_schemas import InterviewEvaluationSchema

load_dotenv()
api_key=os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

def call_gemini_api(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )
    return response.text

def evaluate_interview(prompt: str) -> InterviewEvaluationSchema:
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": InterviewEvaluationSchema.model_json_schema(),
        },
    )

    return InterviewEvaluationSchema.model_validate_json(response.text)
