from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from datetime import date
from ai import answer_task_question, build_task_plan_from_goal, extract_task_items, generate_ai_tasks, get_chat_response
import os

# ==========================
# Load Environment Variables
# ==========================

load_dotenv()

# ==========================
# Flask App
# ==========================

app = Flask(__name__)

app.secret_key = "taskflow_ai_secret"
app.config["SESSION_TYPE"] = "filesystem"

# ==========================
# MySQL Connection
# ==========================

db = None
cursor = None

try:

    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

    cursor = db.cursor(dictionary=True)

    print("✅ Connected to MySQL Successfully")

except Error as e:

    print("❌ Database Connection Error:", e)


# ==========================
# Database Helper Functions
# ==========================

def fetch_query(query, params=()):

    if cursor is None:

        return []

    try:

        cursor.execute(query, params)

        return cursor.fetchall()

    except Error as e:

        print("⚠️ Query Error:", e)

        return []


def fetch_count(query, params=()):

    if cursor is None:

        return 0

    try:

        cursor.execute(query, params)

        row = cursor.fetchone()

        if row:

            return list(row.values())[0]

        return 0

    except Error as e:

        print("⚠️ Count Error:", e)

        return 0
        # ==========================
# Home Page
# ==========================

@app.route("/")
def home():

    today = date.today()

    search = request.args.get("search", "").strip()
    filter_by = request.args.get("filter", "")
    sort_by = request.args.get("sort", "newest")

    if cursor is None:

        flash("⚠️ Database connection is unavailable.", "danger")

        return render_template(
            "index.html",
            tasks=[],
            total=0,
            completed=0,
            pending=0,
            progress=0,
            high_priority=0,
            due_today=0,
            overdue=0,
            search=search,
            filter_by=filter_by,
            sort_by=sort_by,
            today=today,
            chat_history=session.get("chat_history", [])
        )

    # ==========================
    # Search + Filter + Sorting
    # ==========================

    query = "SELECT * FROM tasks WHERE 1=1"

    params = []

    if search:

        query += " AND title LIKE %s"

        params.append("%" + search + "%")

    if filter_by == "completed":

        query += " AND status=1"

    elif filter_by == "pending":

        query += " AND status=0"

    elif filter_by == "high":

        query += " AND priority='High'"

    elif filter_by == "medium":

        query += " AND priority='Medium'"

    elif filter_by == "low":

        query += " AND priority='Low'"

    if sort_by == "oldest":

        query += " ORDER BY id ASC"

    elif sort_by == "priority":

        query += """
        ORDER BY
        CASE
            WHEN priority='High' THEN 1
            WHEN priority='Medium' THEN 2
            WHEN priority='Low' THEN 3
            ELSE 4
        END
        """

    elif sort_by == "due":

        query += " ORDER BY due_date ASC"

    else:

        query += " ORDER BY id DESC"

    tasks = fetch_query(
        query,
        tuple(params)
    )

    # ==========================
    # Dashboard Statistics
    # ==========================

    total = fetch_count(
        "SELECT COUNT(*) FROM tasks"
    )

    completed = fetch_count(
        "SELECT COUNT(*) FROM tasks WHERE status=1"
    )

    pending = total - completed

    high_priority = fetch_count(
        "SELECT COUNT(*) FROM tasks WHERE priority='High'"
    )

    due_today = fetch_count(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE due_date=%s
        AND status=0
        """,
        (today,)
    )

    overdue = fetch_count(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE due_date<%s
        AND status=0
        """,
        (today,)
    )

    progress = 0

    if total > 0:

        progress = int(
            (completed / total) * 100
        )

    # ==========================
    # Due Today / Overdue
    # ==========================

    for task in tasks:

        task["is_today"] = False
        task["is_overdue"] = False

        if task["status"] == 0 and task["due_date"]:

            if task["due_date"] == today:

                task["is_today"] = True

            elif task["due_date"] < today:

                task["is_overdue"] = True

    return render_template(

        "index.html",

        tasks=tasks,

        total=total,

        completed=completed,

        pending=pending,

        progress=progress,

        high_priority=high_priority,

        due_today=due_today,

        overdue=overdue,

        search=search,

        filter_by=filter_by,

        sort_by=sort_by,

        today=today,

        chat_history=session.get("chat_history", [])

    )
    # ==========================
# AI Task Generator
# ==========================

@app.route("/generate", methods=["POST"])
def generate():

    goal = request.form.get("goal", "").strip()

    if not goal:

        flash("⚠️ Please enter your goal first.", "warning")

        return redirect(url_for("home"))

    if cursor is None:

        flash("⚠️ Database connection is unavailable, so AI tasks could not be saved.", "warning")

        return redirect(url_for("home"))

    ai_response = generate_ai_tasks(goal)

    if not ai_response:

        flash("⚠️ AI could not generate tasks.", "danger")

        return redirect(url_for("home"))

    tasks = extract_task_items(ai_response)

    if not tasks:

        flash("⚠️ AI did not return any task suggestions.", "warning")

        return redirect(url_for("home"))

    task_plan = build_task_plan_from_goal(goal)

    if task_plan:

        planned_tasks = []

        for idx, task in enumerate(tasks):
            item = task_plan[idx] if idx < len(task_plan) else task_plan[-1]
            planned_tasks.append({
                "title": task,
                "priority": item.get("priority", "Medium"),
                "due_date": item.get("due_date"),
            })

    else:

        planned_tasks = [
            {
                "title": task,
                "priority": "Medium",
                "due_date": None,
            }
            for task in tasks
        ]

    added = 0

    try:

        for task in planned_tasks:

            cursor.execute(
                """
                INSERT INTO tasks
                (
                    title,
                    priority,
                    due_date,
                    status
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    task["title"],
                    task["priority"],
                    task.get("due_date"),
                    0
                )
            )

            added += 1

        db.commit()

        flash(
            f"🤖 AI generated {added} tasks successfully!",
            "success"
        )

    except Error as e:

        print("AI Insert Error:", e)

        flash(
            "⚠️ Unable to save AI tasks.",
            "danger"
        )

    return redirect(url_for("home"))


# ==========================
# Ask AI About Tasks
# ==========================

@app.route("/ask-ai", methods=["POST"])
def ask_ai():

    question = request.form.get("question", "").strip()
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if not question:
        message = "Please ask a question about your tasks and I’ll help you plan them clearly."

        if is_ajax:
            return jsonify({"answer": message})

        flash("⚠️ Please ask a question about your tasks.", "warning")
        return redirect(url_for("home"))

    tasks = []

    if cursor is not None:

        try:

            cursor.execute(
                "SELECT * FROM tasks ORDER BY id DESC"
            )

            tasks = cursor.fetchall()

        except Error as e:

            print("Ask AI Error:", e)

    history = session.get("chat_history", [])

    try:
        answer = get_chat_response(question, tasks, history)
    except Exception as e:
        print("Ask AI Response Error:", e)
        answer = "I’m sorry, I had trouble preparing a response. Please try again."

    session["chat_history"] = history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer}
    ]

    if is_ajax:
        return jsonify({"answer": answer})

    flash("🤖 AI response ready.", "info")

    return redirect(url_for("home"))


# ==========================
# Add Task
# ==========================

@app.route("/add", methods=["POST"])
def add():

    title = request.form.get("task", "").strip()

    priority = request.form.get("priority") or "Medium"

    due_date = request.form.get("due_date")

    if not title:

        flash("⚠️ Task title is required.", "warning")

        return redirect(url_for("home"))

    try:

        cursor.execute(
            """
            INSERT INTO tasks
            (
                title,
                priority,
                due_date,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                title,
                priority,
                due_date if due_date else None,
                0
            )
        )

        db.commit()

        flash(
            "✅ Task Added Successfully!",
            "success"
        )

    except Error as e:

        print(e)

        flash(
            "⚠️ Unable to add task.",
            "danger"
        )

    return redirect(url_for("home"))


# ==========================
# Toggle Task
# ==========================

@app.route("/toggle/<int:id>")
def toggle(id):

    try:

        cursor.execute(
            """
            UPDATE tasks
            SET status = NOT status
            WHERE id=%s
            """,
            (id,)
        )

        db.commit()

        flash(
            "✔️ Task Updated Successfully!",
            "info"
        )

    except Error as e:

        print(e)

        flash(
            "⚠️ Unable to update task.",
            "danger"
        )

    return redirect(url_for("home"))


# ==========================
# Delete Task
# ==========================

@app.route("/delete/<int:id>")
def delete(id):

    try:

        cursor.execute(
            """
            DELETE FROM tasks
            WHERE id=%s
            """,
            (id,)
        )

        db.commit()

        flash(
            "🗑️ Task Deleted Successfully!",
            "danger"
        )

    except Error as e:

        print(e)

        flash(
            "⚠️ Unable to delete task.",
            "danger"
        )

    return redirect(url_for("home"))
    # ==========================
# Edit Task
# ==========================

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    if cursor is None:

        flash("⚠️ Database connection unavailable.", "danger")

        return redirect(url_for("home"))

    if request.method == "POST":

        title = request.form.get("task", "").strip()

        priority = request.form.get("priority") or "Medium"

        due_date = request.form.get("due_date")

        if not title:

            flash(
                "⚠️ Task title is required.",
                "warning"
            )

            return redirect(url_for("edit", id=id))

        try:

            cursor.execute(
                """
                UPDATE tasks

                SET

                    title=%s,

                    priority=%s,

                    due_date=%s

                WHERE id=%s
                """,
                (
                    title,
                    priority,
                    due_date if due_date else None,
                    id
                )
            )

            db.commit()

            flash(
                "✏️ Task Updated Successfully!",
                "success"
            )

            return redirect(url_for("home"))

        except Error as e:

            print("Edit Error:", e)

            flash(
                "⚠️ Unable to update task.",
                "danger"
            )

            return redirect(url_for("edit", id=id))

    try:

        cursor.execute(
            """
            SELECT *
            FROM tasks
            WHERE id=%s
            """,
            (id,)
        )

        task = cursor.fetchone()

    except Error as e:

        print("Fetch Error:", e)

        flash(
            "⚠️ Unable to fetch task.",
            "danger"
        )

        return redirect(url_for("home"))

    if not task:

        flash(
            "⚠️ Task not found.",
            "warning"
        )

        return redirect(url_for("home"))

    return render_template(
        "edit.html",
        task=task
    )


# ==========================
# Run Application
# ==========================

if __name__ == "__main__":

    app.run(
        debug=True
    )