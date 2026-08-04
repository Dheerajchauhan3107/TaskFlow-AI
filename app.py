from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
from datetime import date

# ==========================
# Load Environment Variables
# ==========================

load_dotenv()

app = Flask(__name__)

# Flash Message Secret Key
app.secret_key = "taskflow_ai_secret"

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


def fetch_query(query, params=()):
    if cursor is None:
        return []

    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    except Error as e:
        print("⚠️ Query error:", e)
        return []


def fetch_count(query, params=()):
    if cursor is None:
        return 0

    try:
        cursor.execute(query, params)
        row = cursor.fetchone()
        if row is None:
            return 0
        return next(iter(row.values()), 0)
    except Error as e:
        print("⚠️ Count query error:", e)
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
            search=search,
            filter_by=filter_by,
            sort_by=sort_by,
            high_priority=0,
            due_today=0,
            overdue=0,
            today=today,
        )

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

    tasks = fetch_query(query, tuple(params))

    total = fetch_count("SELECT COUNT(*) AS total FROM tasks")
    completed = fetch_count("SELECT COUNT(*) AS completed FROM tasks WHERE status=1")
    pending = total - completed

    high_priority = fetch_count(
        "SELECT COUNT(*) FROM tasks WHERE priority = 'High'"
    )

    due_today = fetch_count(
        """
        SELECT COUNT(*) AS due_today
        FROM tasks
        WHERE due_date=%s
        AND status=0
        """,
        (today,)
    )

    overdue = fetch_count(
        """
        SELECT COUNT(*) AS overdue
        FROM tasks
        WHERE due_date < %s
        AND status=0
        """,
        (today,)
    )

    progress = 0
    if total > 0:
        progress = int((completed / total) * 100)

    for task in tasks:
        task["is_overdue"] = False
        task["is_today"] = False

        if task["due_date"] and task["status"] == 0:
            if task["due_date"] < today:
                task["is_overdue"] = True
            elif task["due_date"] == today:
                task["is_today"] = True

    return render_template(
        "index.html",
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending,
        progress=progress,
        search=search,
        filter_by=filter_by,
        sort_by=sort_by,
        high_priority=high_priority,
        due_today=due_today,
        overdue=overdue,
        today=today,
    )


# ==========================
# Add Task
# ==========================

@app.route("/add", methods=["POST"])
def add():
    if cursor is None:
        flash("⚠️ Database connection is unavailable.", "danger")
        return redirect(url_for("home"))

    title = request.form.get("task", "").strip()
    if title:
        priority = request.form.get("priority") or "Medium"
        due_date = request.form.get("due_date")
        try:
            cursor.execute(
                """
                INSERT INTO tasks (title, priority, due_date, status)
                VALUES (%s, %s, %s, %s)
                """,
                (title, priority, due_date if due_date else None, 0),
            )
            db.commit()
            flash("✅ Task Added Successfully!", "success")
        except Error as e:
            print("⚠️ Add task error:", e)
            flash("⚠️ Unable to add task right now.", "danger")
    else:
        flash("⚠️ Task title is required.", "danger")

    return redirect(url_for("home"))


# ==========================
# Toggle Complete
# ==========================

@app.route("/toggle/<int:id>")
def toggle(id):
    if cursor is None:
        flash("⚠️ Database connection is unavailable.", "danger")
        return redirect(url_for("home"))

    try:
        cursor.execute(
            """
            UPDATE tasks
            SET status = NOT status
            WHERE id=%s
            """,
            (id,),
        )
        db.commit()
        flash("✔️ Task Status Updated!", "info")
    except Error as e:
        print("⚠️ Toggle task error:", e)
        flash("⚠️ Unable to update task status right now.", "danger")
    return redirect(url_for("home"))


# ==========================
# Delete Task
# ==========================

@app.route("/delete/<int:id>")
def delete(id):
    if cursor is None:
        flash("⚠️ Database connection is unavailable.", "danger")
        return redirect(url_for("home"))

    try:
        cursor.execute(
            """
            DELETE FROM tasks
            WHERE id=%s
            """,
            (id,),
        )
        db.commit()
        flash("🗑️ Task Deleted Successfully!", "danger")
    except Error as e:
        print("⚠️ Delete task error:", e)
        flash("⚠️ Unable to delete task right now.", "danger")
    return redirect(url_for("home"))


# ==========================
# Edit Task
# ==========================

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if request.method == "POST":
        title = request.form.get("task", "").strip()
        priority = request.form.get("priority") or "Medium"
        due_date = request.form.get("due_date")

        if title:
            if cursor is None:
                flash("⚠️ Database connection is unavailable.", "danger")
                return redirect(url_for("home"))

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
                        id,
                    ),
                )
                db.commit()
                flash("✏️ Task Updated Successfully!", "warning")
                return redirect(url_for("home"))
            except Error as e:
                print("⚠️ Edit task error:", e)
                flash("⚠️ Unable to update task right now.", "danger")
                return redirect(url_for("home"))

        flash("⚠️ Task title is required.", "danger")
        return redirect(url_for("home"))

    cursor.execute(
        """
        SELECT *
        FROM tasks
        WHERE id=%s
        """,
        (id,),
    )
    task = cursor.fetchone()

    if not task:
        return redirect(url_for("home"))

    return render_template("edit.html", task=task)


# ==========================
# Run Application
# ==========================

if __name__ == "__main__":
    app.run(debug=True)