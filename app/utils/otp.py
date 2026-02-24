import random

def generate_otp(length: int = 6) -> str:
    return str(random.randint(10**(length-1), 10**length - 1))
