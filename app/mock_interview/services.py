

def generate_first_question(interview_type: str, difficulty: str, mode: str):
    return f"Tell me about yourself and your experience with {interview_type}."

def build_interview_prompt(interview,conversation: str) -> str:
    return f"""
    You are conducting a {interview.interview_type} interview.
    Difficluty : {interview.difficulty}
    Mode : {interview.mode}

    conversation so far:
    {conversation}

    continue the interview by asking the next question or giving feedback.maintain a natural flow
    Do not give huge explanation for questions or feedbacks
    Keep your questions and feedback concise and to the point.

    """
def build_evaluation_prompt(interview,conversation:str)->str:
        return f"""
You are a senior technical interviewer.

Evaluate the following interview honestly.

Interview type: {interview.interview_type}
Difficulty: {interview.difficulty}
Mode : {interview.mode}

Conversation:
{conversation}

Return STRICT JSON:
{{
  "score": number (0-10),
  "strengths": [string],
  "weaknesses": [string],
  "improvements": [string],
  "final_verdict": string
}}
"""
    