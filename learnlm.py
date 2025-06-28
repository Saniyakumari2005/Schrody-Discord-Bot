import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load API keys
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise Exception("Missing GEMINI_API_KEY. Please add it to your .env file.")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

def ask_learnlm(prompt):
    """Send a user query to Gemini API and return the response."""
    try:
        # Initialize the model
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Create a tutoring context for better responses
        tutoring_prompt = f"""You are Schrody, a helpful AI tutoring assistant. Your role is to:
- Provide clear, educational explanations
- Break down complex topics into understandable parts
- Ask follow-up questions to ensure understanding
- Encourage learning and critical thinking

Student question: {prompt}

Please provide a helpful, educational response:"""

        # Generate response with timeout handling
        response = model.generate_content(tutoring_prompt)

        if response and response.text:
            return response.text
        else:
            return "❌ I received an empty response. Please try rephrasing your question."

    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return f"❌ Sorry, I encountered an error while processing your request: {str(e)[:100]}... Please try again."