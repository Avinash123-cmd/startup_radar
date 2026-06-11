import requests
import json

def generate_ai_startup(gap):

    prompt = f"""
    Market Category: {gap['category']}

    Gap Score: {gap['gap_score']}

    Generate:

    1 Startup Name
    2 Problem
    3 Solution
    4 Pricing
    5 MVP Features
    6 Target Customer
    7 Revenue Model

    Return JSON only.
    """

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model":"llama3",
            "prompt":prompt,
            "stream":False
        }
    )

    return response.json()