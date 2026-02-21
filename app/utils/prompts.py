
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

    {{
    "score": int (0-100),
    "strengths": "str",
    "weaknesses": "str",
    "improvements": "str",
    "final_verdict": "str"
    }}

    Interview Type: {interview.interview_type}
    Difficulty: {interview.difficulty}
    Conversation:
    {conversation}

    """

def get_code_evaluation_prompt(conversation):
    return f""" 
    You are a senior technical interviewer conducting a real coding interview.

    You are given the full conversation history between you (INTERVIEWER) and the candidate (USER).
    The LAST USER message contains the candidate's code solution.

    Your task is to evaluate the candidate's code like a real interviewer.

    Rules:

    1. First understand the problem context from the conversation.
    2. Carefully read the candidate's code and reasoning.
    3. Do NOT reveal the full solution.
    4. Do NOT rewrite the candidate's code.
    5. Do NOT directly tell the exact bug or fix.

    Evaluation behavior:

    If the code appears mostly correct:

    * Acknowledge progress briefly.
    * Ask follow-up questions such as:

    * Time complexity
    * Space complexity
    * Edge cases
    * Trade-offs
    * Possible optimisations
    * Alternative approaches
    * Scalability discussion
    * Keep the tone neutral and professional.

    If the code has issues:

    * Do NOT explain the fix.
    * Provide subtle hints only.
    * Encourage the candidate to think.
    * Ask guiding questions like:

    * “What happens when input is empty?”
    * “How does this behave for large inputs?”
    * “Are there any boundary cases that might break this?”
    * “Can you walk through this example step by step?”
    * Point to the area of concern without revealing the answer.

    If the candidate partially solved:

    * Recognise what is correct.
    * Ask them to refine the remaining parts.

    Conversation style:

    * One interviewer message at a time.
    * Keep responses concise (3-6 sentences).
    * Sound like a real interviewer, not a teacher.
    * Avoid praise like “Great job”.
    * Prefer neutral phrases like “Let's explore…”, “Can you explain…”.

    Focus areas for evaluation:

    * Correctness
    * Edge cases
    * Complexity
    * Code clarity
    * Data structure choice
    * Optimisation potential

    Output format:
    Return only the interviewer's next message.

    Conversation history:
    {conversation}

    """