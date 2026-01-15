
from .gemini import call_gemini_api
def get_next_interviewer_message(prompt: str) -> str:
    response = call_gemini_api(prompt)
    return response


def build_conversation(turns):
    lines = []
    for t in turns:
        if t.role == "USER":
            lines.append(f"Candidate: {t.content}")
        else:
            lines.append(f"Interviewer: {t.content}")
    return "\n".join(lines)
