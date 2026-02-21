
from .gemini import call_gemini_api,evaluate_interview
async def get_next_interviewer_message(prompt: str) -> str:
    response = await call_gemini_api(prompt)
    return response

async def get_evaluation_interview(prompt: str):
    response = await evaluate_interview(prompt)
    return response


def build_conversation(turns):
    lines = []
    for t in turns:
        if t.role == "USER":
            lines.append(f"Candidate: {t.content}")
        else:
            lines.append(f"Interviewer: {t.content}")
    return "\n".join(lines)

def build_conversation_for_eval(turns):
    lines = []
    user_count=0
    interviewer_count=0
    for t in turns:
        if t.role == "USER":
            user_count+=1
            lines.append(f"Candidate: {t.content}")
        else:
            interviewer_count+=1
            lines.append(f"Interviewer: {t.content}")
    if user_count<2 or interviewer_count<1:
        return None
    return "\n".join(lines)


