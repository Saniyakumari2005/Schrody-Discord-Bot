import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Optional

# Load API keys
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise Exception("Missing GEMINI_API_KEY. Please add it to your .env file.")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Shared system prompt for the tutor
TUTOR_SYSTEM_PROMPT = """You are Schrödy, a friendly and supportive tutor with access to current information through web search. Your goal is to help students understand concepts by guiding them through a topic, not by giving them the answer directly.

**Your Persona:**
* **Encouraging and patient:** Maintain a warm and positive tone.
* **Adaptive:** Adjust your language and the complexity of your explanations to the student's level of understanding.
* **Inquisitive:** Ask questions to gauge the student's knowledge and to prompt deeper thinking.
* **Current and accurate:** Use web search when you need current information, recent developments, or when your knowledge might be outdated.

**Your Methodology:**
* **Start by asking:** Begin by asking the student what topic they need help with.
* **One step at a time:** Break down complex topics into smaller, manageable steps. Present only one concept or question per turn to avoid overwhelming the student.
* **Guide, don't tell:** Use guiding questions and analogies to help the student arrive at the answer themselves.
* **Encourage critical thinking:** Prompt the student to explain their reasoning. If they are correct, affirm their understanding. If they are incorrect, gently guide them toward the correct answer.
* **Provide feedback:** Offer clear and constructive feedback.
* **Active recall:** After a few questions, ask the student to summarize what they have learned.
* **Adapt to the student's pace:** If a student wants to move on, provide the correct answer and proceed. If they wish to explore a concept in more detail, engage in a deeper conversation to help them build a comprehensive understanding.
* **Use current information:** When discussing recent events, current statistics, or evolving topics, search for up-to-date information to provide accurate guidance.

**Output Formatting:**
* **Bitesized:** Provide shorter bitesized outputs over longer explanation, unless the student specifically asks for it.
* **Mathematics:** ALWAYS use Unicode symbols for mathematical expressions since LaTeX is not supported in Discord:
  - Use × for multiplication (not *)
  - Use ÷ for division (not /)
  - Use ² ³ ⁴ for superscripts
  - Use ₁ ₂ ₃ for subscripts
  - Use √ for square root
  - Use π for pi
  - Use ∞ for infinity
  - Use ≤ ≥ ≠ ≈ for comparison operators
  - Use ∫ for integration
  - Use Σ for summation
  - Use ∂ for partial derivatives
  - Use α β γ δ θ λ μ σ etc. for Greek letters
* **Formatting:** Use Discord-friendly formatting (bold with **text**, italic with *text*, code with `text`)
* **No LaTeX:** Never use LaTeX syntax like $x^2$ or \\frac{}{} - always use Unicode equivalents

**Web Search Guidelines:**
* When you have access to current information through grounding, use it to provide accurate, up-to-date answers
* Always cite sources when using web-sourced information
* Combine searched information with your tutoring approach

Remember and reference previous parts of the conversation when relevant."""

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

def ask_learnlm(prompt: str, search_enabled: bool = False) -> str:
    """Send a user query to Gemini API and return the response with optional grounding."""
    try:
        # Configure tools based on search_enabled flag
        tools = []
        if search_enabled:
            # Configure grounding with Google Search
            grounding_config = {
                "google_search_retrieval": {
                    "dynamic_retrieval_config": {
                        "mode": "MODE_DYNAMIC",
                        "dynamic_threshold": 0.7
                    }
                }
            }
            tools.append(grounding_config)

        # Initialize the model
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Create the full prompt with system instructions and user input
        full_prompt = f"{TUTOR_SYSTEM_PROMPT}\n\nStudent: {prompt}\n\nTutor:"

        # Generate response with or without grounding
        if tools:
            response = model.generate_content(full_prompt, tools=tools)
        else:
            response = model.generate_content(full_prompt)

        if response and response.text:
            return response.text
        else:
            return "❌ I received an empty response. Please try rephrasing your question."

    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return f"❌ Sorry, I encountered an error while processing your request: {str(e)} Please try again."

def ask_learnlm_with_search(prompt: str) -> str:
    """Wrapper function that explicitly enables search using Gemini grounding."""
    return ask_learnlm(prompt, search_enabled=True)

def ask_learnlm_auto_search(prompt: str) -> str:
    """Automatically determine if search is needed based on prompt content."""
    # Keywords that suggest current information is needed
    search_keywords = [
        "current", "recent", "latest", "today", "now", "2024", "2025", 
        "news", "update", "updated", "development", "breakthrough", 
        "trending", "this year", "this month", "recently", "web", "search", "look up"
    ]

    # Check if any search keywords are present
    should_search = any(keyword in prompt.lower() for keyword in search_keywords)

    return ask_learnlm(prompt, search_enabled=should_search)

class LearnLMTutor:
    """A class-based interface for the LearnLM tutor with grounding capabilities."""

    def __init__(self, model_name: str = 'gemini-2.5-flash'):
        """Initialize the tutor with a specific model."""
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        self.conversation_history = []

        # Grounding configuration
        self.grounding_config = {
            "google_search_retrieval": {
                "dynamic_retrieval_config": {
                    "mode": "MODE_DYNAMIC",
                    "dynamic_threshold": 0.7
                }
            }
        }

    def ask(self, prompt: str, use_search: bool = False, remember_context: bool = True) -> str:
        """Ask a question to the tutor with optional search and context memory."""
        try:
            # Build context from conversation history
            context = ""
            if remember_context and self.conversation_history:
                context = "Previous conversation context:\n"
                for entry in self.conversation_history[-3:]:  # Keep last 3 exchanges
                    context += f"Student: {entry['question']}\nTutor: {entry['answer']}\n\n"

            # Build full prompt
            full_prompt = f"{TUTOR_SYSTEM_PROMPT}\n\n{context}Student: {prompt}\n\nTutor:"

            # Generate response with or without grounding
            if use_search:
                response = self.model.generate_content(full_prompt, tools=[self.grounding_config])
            else:
                response = self.model.generate_content(full_prompt)

            if response and response.text:
                answer = response.text

                # Store in conversation history
                if remember_context:
                    self.conversation_history.append({
                        'question': prompt,
                        'answer': answer
                    })

                return answer
            else:
                return "❌ I received an empty response. Please try rephrasing your question."

        except Exception as e:
            print(f"Error with Gemini API: {e}")
            return f"❌ Sorry, I encountered an error while processing your request: {str(e)} Please try again."

    def ask_with_search(self, prompt: str) -> str:
        """Ask a question with search enabled."""
        return self.ask(prompt, use_search=True)

    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []

    def get_history(self) -> list:
        """Get the conversation history."""
        return self.conversation_history.copy()

# Example usage functions
def demo_math_formatting():
    """Demonstrate proper Unicode math formatting."""
    examples = [
        "Quadratic formula: x = (-b ± √(b² - 4ac)) / 2a",
        "Pythagorean theorem: a² + b² = c²",
        "Euler's identity: e^(iπ) + 1 = 0",
        "Integration: ∫₀^∞ e^(-x²) dx = √π/2",
        "Summation: Σₙ₌₁^∞ 1/n² = π²/6"
    ]

    print("Math formatting examples:")
    for example in examples:
        print(f"✓ {example}")

if __name__ == "__main__":
    # Demo the math formatting
    demo_math_formatting()

    # Example queries
    print("\n" + "="*50)
    print("Example with Gemini grounding:")
    result = ask_learnlm_with_search("What are the latest developments in quantum computing in 2025?")
    print(result)

    print("\n" + "="*50)
    print("Example with class-based interface:")
    tutor = LearnLMTutor()
    result = tutor.ask_with_search("What are the current trends in artificial intelligence education?")
    print(result)