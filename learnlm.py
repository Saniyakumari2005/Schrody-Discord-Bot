import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Optional, List, Dict

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

class LearnLMTutor:
    """A streamlined tutor interface with unified search handling."""

    # Class-level search configuration - shared across all instances
    SEARCH_CONFIG = {
        "google_search_retrieval": {
            "dynamic_retrieval_config": {
                "mode": "MODE_DYNAMIC",
                "dynamic_threshold": 0.7
            }
        }
    }

    # Keywords that suggest current information is needed
    SEARCH_KEYWORDS = [
        "current", "recent", "latest", "today", "now", "2024", "2025", 
        "news", "update", "updated", "development", "breakthrough", 
        "trending", "this year", "this month", "recently", "web", "search", "look up"
    ]

    def __init__(self, model_name: str = 'gemini-2.5-flash'):
        """Initialize the tutor with a specific model."""
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        self.conversation_history = []

    def _should_search(self, prompt: str) -> bool:
        """Determine if search should be enabled based on prompt content."""
        return any(keyword in prompt.lower() for keyword in self.SEARCH_KEYWORDS)

    def _build_context(self, max_history: int = 3) -> str:
        """Build conversation context from history."""
        if not self.conversation_history:
            return ""

        context = "Previous conversation context:\n"
        for entry in self.conversation_history[-max_history:]:
            context += f"Student: {entry['question']}\nTutor: {entry['answer']}\n\n"
        return context

    def ask(self, prompt: str, use_search: Optional[bool] = None, remember_context: bool = True) -> str:
        """
        Ask a question to the tutor.

        Args:
            prompt: The student's question
            use_search: Force search on/off. If None, auto-determines based on content
            remember_context: Whether to remember this exchange in conversation history
        """
        try:
            # Auto-determine search if not specified
            if use_search is None:
                use_search = self._should_search(prompt)

            # Build context from conversation history
            context = self._build_context() if remember_context else ""

            # Build full prompt
            full_prompt = f"{TUTOR_SYSTEM_PROMPT}\n\n{context}Student: {prompt}\n\nTutor:"

            # Generate response with or without grounding
            tools = [self.SEARCH_CONFIG] if use_search else []
            response = self.model.generate_content(full_prompt, tools=tools)

            if response and response.text:
                answer = response.text

                # Store in conversation history
                if remember_context:
                    self.conversation_history.append({
                        'question': prompt,
                        'answer': answer,
                        'used_search': use_search
                    })

                return answer
            else:
                return "❌ I received an empty response. Please try rephrasing your question."

        except Exception as e:
            print(f"Error with Gemini API: {e}")
            return f"❌ Sorry, I encountered an error while processing your request: {str(e)} Please try again."

    def ask_with_search(self, prompt: str) -> str:
        """Ask a question with search explicitly enabled."""
        return self.ask(prompt, use_search=True)

    def ask_without_search(self, prompt: str) -> str:
        """Ask a question with search explicitly disabled."""
        return self.ask(prompt, use_search=False)

    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []

    def get_history(self) -> List[Dict]:
        """Get the conversation history."""
        return self.conversation_history.copy()

    def list_models(self) -> str:
        """List all available Gemini models."""
        try:
            models = genai.list_models()
            model_list = []
            for model in models:
                model_list.append(f"• **{model.name}** - {model.description}")
            return "\n".join(model_list) if model_list else "No models available"
        except Exception as e:
            return f"❌ Error listing models: {str(e)}"

# Convenience functions for backwards compatibility
def ask_learnlm(prompt: str, search_enabled: bool = False) -> str:
    """Legacy function wrapper for backwards compatibility."""
    tutor = LearnLMTutor()
    return tutor.ask(prompt, use_search=search_enabled, remember_context=False)

def ask_learnlm_with_search(prompt: str) -> str:
    """Legacy function wrapper with search enabled."""
    tutor = LearnLMTutor()
    return tutor.ask_with_search(prompt)

def ask_learnlm_auto_search(prompt: str) -> str:
    """Legacy function wrapper with auto search detection."""
    tutor = LearnLMTutor()
    return tutor.ask(prompt, remember_context=False)

# Demo function
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

    # Example with streamlined interface
    print("\n" + "="*50)
    print("Example with streamlined interface:")
    tutor = LearnLMTutor()

    # Auto-search detection
    result = tutor.ask("What are the latest developments in quantum computing in 2025?")
    print("Auto-search result:", result[:100] + "..." if len(result) > 100 else result)

    # Explicit search control
    result = tutor.ask_with_search("Current trends in AI education")
    print("Explicit search result:", result[:100] + "..." if len(result) > 100 else result)

    # No search
    result = tutor.ask_without_search("Explain the quadratic formula")
    print("No search result:", result[:100] + "..." if len(result) > 100 else result)