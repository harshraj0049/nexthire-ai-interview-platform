
from . gemini import client
from google.genai import types
import json
def summarize_resume_with_gemini(
    *,
    file_bytes: bytes,
    mime_type: str,
) -> dict:
    prompt = """
    You are an expert technical interviewer.

    Analyze the provided resume document and produce a compact,
    high-signal summary optimized for repeated use as interview context.

    Your goal is to extract only what materially affects:
    - question selection
    - difficulty calibration
    - probing depth
    - follow-up reasoning

    Output a concise JSON object with these sections:
    - candidate_overview
    - core_skills
    - key_strengths
    - project_signal
    - interview_flags

    Guidelines:
    - Be brief and information-dense
    - Prefer abstraction over description
    - Do not reproduce resume wording
    - Do not include dates, institutions, locations, links, or personal details
    - Omit any section if information is weak or missing

    STRICT RULES:
    - Output valid JSON only
    - No markdown, no explanations
    - Keep the total response under 2000 characters
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(
                data=file_bytes,
                mime_type=mime_type,
            ),
            prompt,
        ],
    )

    # Gemini sometimes wraps JSON in markdown
    text = response.text.strip()

    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError("Gemini returned invalid JSON")
