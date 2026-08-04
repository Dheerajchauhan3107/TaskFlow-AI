import os
import re
import warnings
from datetime import date
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


def _build_model():
    if genai is None:
        return None

    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        return genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        print("⚠️ Gemini AI setup warning:", e)
        return None


model = _build_model()


def extract_task_items(response):
    if not response:
        return []

    tasks = []

    for raw_line in str(response).splitlines():
        line = raw_line.strip()

        if not line:
            continue

        line = re.sub(r"^[-*•]\s*", "", line)
        line = re.sub(r"^\d+[.)]\s*", "", line)
        line = line.strip(" -•")

        if not line:
            continue

        if line.lower().startswith(("here are", "task list", "tasks:", "goals:")):
            continue

        tasks.append(line)

    return tasks


def _fallback_tasks(goal):
    goal_text = (goal or "your goal").strip()
    lowered = goal_text.lower()

    if any(keyword in lowered for keyword in ["study", "learn", "python", "exam", "cuet", "course"]):
        suggestions = [
            f"Create a study plan for {goal_text}",
            "Gather the best learning resources",
            "Set daily practice time",
            "Track progress every week"
        ]
    elif any(keyword in lowered for keyword in ["website", "app", "project", "build", "startup"]):
        suggestions = [
            f"Define the main goal for {goal_text}",
            "Create a simple project plan",
            "Build the core features first",
            "Test and improve the result"
        ]
    elif any(keyword in lowered for keyword in ["fitness", "health", "gym", "workout"]):
        suggestions = [
            f"Set a daily routine for {goal_text}",
            "Prepare your workout or meal plan",
            "Track your consistency",
            "Review your progress weekly"
        ]
    else:
        suggestions = [
            f"Break {goal_text} into small steps",
            "Set a realistic timeline",
            "Start with the first important action",
            "Review progress and adjust as needed"
        ]

    return suggestions[:8]


# ==========================
# AI Task Generator
# ==========================

def build_task_plan_from_goal(goal):
    goal_text = (goal or "").strip()

    if not goal_text:
        return []

    lowered = goal_text.lower()

    if any(keyword in lowered for keyword in ["interview", "exam", "test"]):
        priorities = ["High", "High", "Medium"]
        due_days = [1, 3, 7]
        base_tasks = [
            f"Research {goal_text}",
            "Prepare the key talking points",
            "Practice your delivery"
        ]
    elif any(keyword in lowered for keyword in ["project", "website", "app", "build"]):
        priorities = ["High", "Medium", "Low"]
        due_days = [1, 4, 7]
        base_tasks = [
            f"Define the scope for {goal_text}",
            "Build the first working version",
            "Review and improve the result"
        ]
    elif any(keyword in lowered for keyword in ["study", "learn", "python", "course", "cuet"]):
        priorities = ["High", "Medium", "Medium"]
        due_days = [1, 3, 5]
        base_tasks = [
            f"Create a plan for {goal_text}",
            "Start the first study session",
            "Track your progress"
        ]
    else:
        priorities = ["Medium", "Medium", "Low"]
        due_days = [2, 5, 7]
        base_tasks = [
            f"Break {goal_text} into steps",
            "Start the most important action",
            "Review your progress"
        ]

    tasks = []
    today = date.today()

    for index, title in enumerate(base_tasks[:5]):
        due_date = (today if due_days[index] == 0 else today.replace(day=min(28, today.day + due_days[index])))
        tasks.append({
            "title": title,
            "priority": priorities[index % len(priorities)],
            "due_date": due_date.isoformat(),
            "status": 0,
        })

    return tasks


def generate_ai_tasks(goal):

    goal_text = (goal or "").strip()

    if not goal_text:
        return None

    prompt = f"""
You are an AI Productivity Assistant.

Generate a practical task list for this goal.

Goal:
{goal_text}

Rules:
- Maximum 8 tasks
- One task per line
- No numbering
- No explanation
- Keep every task short
"""

    try:
        if model is None:
            raise RuntimeError("AI model unavailable")

        response = model.generate_content(prompt)
        text = getattr(response, "text", "")

        tasks = extract_task_items(text)
        if tasks:
            return "\n".join(tasks)

    except Exception as e:
        print("Gemini Error:", e)

    fallback_tasks = _fallback_tasks(goal_text)
    return "\n".join(fallback_tasks)


def _normalize_due_date(value):
    if not value:
        return None

    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _is_follow_up(question_text, history):
    if not history:
        return False

    follow_up_markers = ["more", "continue", "tell me more", "and", "also", "what else", "next"]
    return any(marker in question_text for marker in follow_up_markers)


def get_chat_response(question, tasks, history=None):
    if not question:
        return "Please ask something about your tasks and I’ll help you plan them clearly."

    task_list = tasks or []
    question_text = question.strip().lower()
    history = history or []

    greetings = ["hi", "hello", "hey", "hii", "hiii", "hola", "yo", "good morning", "good evening", "good afternoon"]
    if any(greeting in question_text for greeting in greetings):
        return (
            "Hello! I’m your TaskFlow AI assistant. I can help you create tasks, understand your workload, "
            "and suggest a better plan for the day. What would you like to do?"
        )

    if any(keyword in question_text for keyword in ["how are you", "what are you", "who are you", "tell me about yourself"]):
        return (
            "I’m your TaskFlow AI assistant — a helpful productivity companion. I can guide you through your tasks, "
            "answer questions about your progress, and help you stay organized."
        )

    if any(keyword in question_text for keyword in ["thanks", "thank you", "appreciate"]):
        return "You’re welcome! I’m here to help you stay organized and focused."

    if _is_follow_up(question_text, history):
        pending = [task for task in task_list if not task.get("status")]
        if pending:
            names = ", ".join(task.get("title", "Untitled") for task in pending[:3])
            return (
                f"Sure — you still have {len(pending)} pending tasks, including {names}. "
                f"If you want more, a good next step is to focus on the most important one first and keep the momentum going."
            )
        return "You’re all caught up for now. If you want, I can help you plan your next move or create a fresh task list."

    return answer_task_question(question, tasks)


def answer_task_question(question, tasks):
    if not question:
        return "Please ask something about your tasks and I’ll help you plan them clearly."

    task_list = tasks or []
    question_text = question.strip().lower()

    pending = [task for task in task_list if not task.get("status")]
    completed = [task for task in task_list if task.get("status")]
    high_priority = [task for task in task_list if str(task.get("priority") or "").lower() == "high"]

    today = date.today()
    overdue = []
    due_today = []

    for task in task_list:
        due_date = _normalize_due_date(task.get("due_date"))
        if not due_date:
            continue

        if due_date < today:
            overdue.append(task)
        elif due_date == today:
            due_today.append(task)

    if any(keyword in question_text for keyword in ["pending", "not done", "remaining", "to do"]):
        if pending:
            names = ", ".join(task.get("title", "Untitled") for task in pending[:5])
            return (
                f"You still have {len(pending)} pending tasks on your plate, and that’s completely manageable. "
                f"The most important ones right now are: {names}. "
                f"A smart move would be to start with the one that matters most and build momentum from there."
            )
        return "You have no pending tasks right now. That’s a great place to be."

    if any(keyword in question_text for keyword in ["completed", "done", "finished"]):
        if completed:
            names = ", ".join(task.get("title", "Untitled") for task in completed[:5])
            return (
                f"You’ve already completed {len(completed)} tasks, including: {names}. "
                f"That’s excellent progress, and it shows you’re moving forward with focus and consistency."
            )
        return "You have not completed any tasks yet, but every small step still counts."

    if any(keyword in question_text for keyword in ["overdue", "late"]):
        if overdue:
            names = ", ".join(task.get("title", "Untitled") for task in overdue[:5])
            return (
                f"You have {len(overdue)} overdue tasks, such as: {names}. "
                f"The best move now is to reset your focus, tackle the most important one first, and clear the small blockers quickly."
            )
        return "You do not have any overdue tasks at the moment. That means your schedule is in a good shape."

    if any(keyword in question_text for keyword in ["high priority", "priority", "important"]):
        if high_priority:
            names = ", ".join(task.get("title", "Untitled") for task in high_priority[:5])
            return (
                f"Your high-priority tasks are: {names}. "
                f"These deserve your attention first because they have the biggest impact on your goals."
            )
        return "You do not have any high-priority tasks right now, which makes your plan feel lighter and more manageable."

    if any(keyword in question_text for keyword in ["summary", "details", "tell me", "what do i have", "what do i have"]):
        return (
            f"Right now, your task list looks balanced: {len(pending)} pending, {len(completed)} completed, "
            f"{len(overdue)} overdue, and {len(due_today)} due today. "
            f"You’ve got a clear picture of your workload now, and I can help you turn it into a calmer, smarter plan for the day."
        )

    return (
        f"You currently have {len(task_list)} tasks in total. "
        f"There are {len(pending)} still pending, {len(completed)} completed, {len(overdue)} overdue, and {len(due_today)} due today. "
        f"That gives you a clear picture of where your energy should go next, and I’m here to help you make the most of it."
    )