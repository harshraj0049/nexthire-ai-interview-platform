from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key=os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

def call_gemini_api(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemma-3-12b-it",
        contents=prompt
    )
    return response.text
