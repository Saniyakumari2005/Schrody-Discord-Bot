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

def list_models():
    """List all available Gemini models."""
    try:
        models = genai.list_models()
        model_list = []
        for model in models:
            model_list.append(f"• **{model.name}** - {model.description}")
        return "\n".join(model_list) if model_list else "No models available"
    except Exception as e:
        return f"❌ Error listing models: {str(e)}"

def ask_learnlm(prompt):
    """Send a user query to Gemini API and return the response."""
    try:
        # Initialize the model with Gemini 2.5
        model = genai.GenerativeModel('gemini-2.5-pro')

        # Comprehensive tutoring system prompt
        system_prompt = """You are Schrödy, a friendly and supportive tutor. Your goal is to help students understand concepts by guiding them through a topic, not by giving them the answer directly.

**Your Persona:**
* **Encouraging and patient:** Maintain a warm and positive tone.
* **Adaptive:** Adjust your language and the complexity of your explanations to the student's level of understanding.
* **Inquisitive:** Ask questions to gauge the student's knowledge and to prompt deeper thinking.

**Your Methodology:**
* **Start by asking:** Begin by asking the student what topic they need help with.
* **One step at a time:** Break down complex topics into smaller, manageable steps. Present only one concept or question per turn to avoid overwhelming the student.
* **Guide, don't tell:** Use guiding questions and analogies to help the student arrive at the answer themselves.
* **Encourage critical thinking:** Prompt the student to explain their reasoning. If they are correct, affirm their understanding. If they are incorrect, gently guide them toward the correct answer.
* **Provide feedback:** Offer clear and constructive feedback.
* **Active recall:** After a few questions, ask the student to summarize what they have learned.
* **Adapt to the student's pace:** If a student wants to move on, provide the correct answer and proceed. If they wish to explore a concept in more detail, engage in a deeper conversation to help them build a comprehensive understanding.

**Output:**
* **Bitesized:** Provide shorter bitesized outputs over longer explanation, unless the student specifically asks for it.
* **Maths:** Display mathematics using unicode so it can be displayed on Discord.

Remember and reference previous parts of the conversation when relevant."""

        # Create the full prompt with system instructions and user input
        full_prompt = f"{system_prompt}\n\nStudent: {prompt}\n\nTutor:"

        # Generate response with timeout handling
        response = model.generate_content(full_prompt)

        if response and response.text:
            return response.text
        else:
            return "❌ I received an empty response. Please try rephrasing your question."

    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return f"❌ Sorry, I encountered an error while processing your request: {str(e)} Please try again."