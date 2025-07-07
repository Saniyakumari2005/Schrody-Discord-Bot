import os
import google.generativeai as genai
from dotenv import load_dotenv
import requests
import json
from typing import List, Dict, Optional

# Load API keys
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")  
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

if not GEMINI_API_KEY:
    raise Exception("Missing GEMINI_API_KEY. Please add it to your .env file.")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

def search_web(query: str, num_results: int = 3) -> List[Dict]:
    """Search the web using Google Custom Search API."""
    if not SEARCH_API_KEY or not SEARCH_ENGINE_ID:
        return [{"error": "Search API not configured. Please add SEARCH_API_KEY and SEARCH_ENGINE_ID to your .env file."}]

    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': SEARCH_API_KEY,
            'cx': SEARCH_ENGINE_ID,
            'q': query,
            'num': num_results
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        results = []

        if 'items' in data:
            for item in data['items']:
                results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'displayLink': item.get('displayLink', '')
                })

        return results

    except Exception as e:
        return [{"error": f"Search failed: {str(e)}"}]

def format_search_results(results: List[Dict]) -> str:
    """Format search results for the AI model."""
    if not results:
        return "No search results found."

    if results[0].get('error'):
        return f"Search error: {results[0]['error']}"

    formatted = "Search Results:\n\n"
    for i, result in enumerate(results, 1):
        formatted += f"{i}. **{result['title']}**\n"
        formatted += f"   Source: {result['displayLink']}\n"
        formatted += f"   Summary: {result['snippet']}\n"
        formatted += f"   Link: {result['link']}\n\n"

    return formatted

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
    """Send a user query to Gemini API and return the response."""
    try:
        # Initialize the model with Gemini 2.5
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Enhanced tutoring system prompt with search capabilities
        system_prompt = """You are Schrödy, a friendly and supportive tutor with access to current information through web search. Your goal is to help students understand concepts by guiding them through a topic, not by giving them the answer directly.

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
* Search for recent information, current events, updated statistics, or when knowledge might be outdated
* Always cite sources when using searched information
* Combine searched information with your tutoring approach

Remember and reference previous parts of the conversation when relevant."""

        # Check if we should perform a web search
        search_context = ""
        if search_enabled:
            # Simple heuristic to determine if search is needed
            search_keywords = ["current", "recent", "latest", "today", "2024", "2025", "news", "update"]
            should_search = any(keyword in prompt.lower() for keyword in search_keywords)

            if should_search:
                search_results = search_web(prompt)
                search_context = format_search_results(search_results)

        # Create the full prompt with system instructions, search context, and user input
        full_prompt = f"{system_prompt}\n\n"

        if search_context:
            full_prompt += f"Current Information from Web Search:\n{search_context}\n\n"

        full_prompt += f"Student: {prompt}\n\nTutor:"

        # Generate response with timeout handling
        response = model.generate_content(full_prompt)

        if response and response.text:
            return response.text
        else:
            return "❌ I received an empty response. Please try rephrasing your question."

    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return f"❌ Sorry, I encountered an error while processing your request: {str(e)} Please try again."

def ask_learnlm_with_search(prompt: str) -> str:
    """Wrapper function that explicitly enables search."""
    return ask_learnlm(prompt, search_enabled=True)

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
    print("Example with web search:")
    result = ask_learnlm_with_search("What are the latest developments in quantum computing in 2024?")
    print(result)