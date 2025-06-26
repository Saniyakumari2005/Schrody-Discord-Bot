import os
import requests
from dotenv import load_dotenv

# Load API keys
load_dotenv()
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT")

if not LLM_API_KEY or not LLM_ENDPOINT:
    raise Exception("Missing LLM API key or endpoint. Please check your .env file.")

def ask_learnlm(prompt):
    """Send a user query to Google LearnLM and return the response."""
    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
    payload = {"input": prompt}

    response = requests.post(LLM_ENDPOINT, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("output", "Sorry, I couldn't process your request.")
    else:
        return "❌ Error: Failed to fetch response from LearnLM."
