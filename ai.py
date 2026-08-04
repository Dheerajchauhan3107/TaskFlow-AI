import os
import warnings
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=FutureWarning, module="google\.generativeai")

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# ==========================
# Load Environment Variables
# ==========================

load_dotenv()

# ==========================
# Configure Gemini
# ==========================

if genai is not None:
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        print("⚠️ Gemini AI setup warning:", e)
        model = None
else:
    model = None

# ==========================
# AI Task Generator
# ==========================

def generate_ai_tasks(goal):

    prompt = f"""
You are an AI Productivity Assistant.

Generate a practical task list for this goal.

Goal:
{goal}

Rules:
- Maximum 10 tasks
- One task per line
- No numbering
- No explanation
- Keep every task short
"""

    try:
        if model is None:
            return None

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        print("Gemini Error:", e)
        return None