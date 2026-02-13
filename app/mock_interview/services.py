

def generate_first_question(interview_type: str, difficulty: str, mode: str, resume_summary: str = None) -> str:
    if resume_summary:
        return f"Tell me about yourself and your experience with {interview_type} based on your resume."
    return f"Tell me about yourself and your experience with {interview_type}."

def build_interview_prompt(interview,conversation: str,resume_summary:str=None) -> str:
    return f"""
    You are conducting a {interview.interview_type} interview.
    Difficluty : {interview.difficulty}
    Mode : {interview.mode}

    {f"Candidate Resume Summary: {resume_summary}" if resume_summary else "NA"}

    conversation so far:
    {conversation}

    continue the interview by asking the next question or giving feedback.maintain a natural flow
    Do not give huge explanation for questions or feedbacks
    Keep your questions and feedback concise and to the point.

    """

def build_evaluation_prompt(interview, conversation: str) -> str:
    return f"""
    You are a senior technical interviewer.

    Evaluate the candidate based ONLY on the conversation below.

    Rules:
    1. If the candidate gave incomplete answers, reduce score significantly.
    2. If logic is weak, deduct heavily.
    3. If no optimization discussion, deduct.
    4. If no time/space complexity discussion, deduct.
    5. If user gave only clarifications but no final answer, treat as weak performance.
    6. Do NOT inflate scores.

    Scoring guidelines:
    90-100 → Exceptional (clear, optimized, confident)
    70-89  → Good but improvable
    50-69  → Average, multiple gaps
    30-49  → Weak understanding
    0-29   → No attempt or very poor attempt

    Return response strictly in JSON format:

    {
    "score": int (0-100),
    "strengths": "string",
    "weaknesses": "string",
    "improvements": "string",
    "final_verdict": "string"
    }
    
    Interview Type: {interview.interview_type}
    Difficulty: {interview.difficulty}
    Conversation:
    {conversation}

    """

    