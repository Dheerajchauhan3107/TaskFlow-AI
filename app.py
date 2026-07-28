from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# ==========================
# Load Environment Variables
# ==========================

load_dotenv()

app = Flask(__name__)

# ==========================
# MySQL Connection
# ==========================

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
# Home Page
# ==========================

@app.route("/")
def home():

    cursor.execute("SELECT * FROM tasks ORDER BY id DESC")
    tasks = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS total FROM tasks")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS completed FROM tasks WHERE status=1")
    completed = cursor.fetchone()["completed"]

    pending = total - completed

    progress = 0
    if total > 0:
        progress = int((completed / total) * 100)

    return render_template(
        "index.html",
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending,
        progress=progress
    )


# ==========================
# Add Task
# ==========================

@app.route("/add", methods=["POST"])
def add():

    task = request.form.get("task")
    priority = request.form.get("priority")
    due_date = request.form.get("due_date")

    if task and task.strip():

        cursor.execute(
            """
            INSERT INTO tasks(title, priority, due_date)
            VALUES(%s, %s, %s)
            """,
            (
                task.strip(),
                priority,
                due_date if due_date else None
            )
        )

        db.commit()

    return redirect(url_for("home"))


# ==========================
# Delete Task
# ==========================

@app.route("/delete/<int:id>")
def delete(id):

    cursor.execute(
        "DELETE FROM tasks WHERE id=%s",
        (id,)
    )

    db.commit()

    return redirect(url_for("home"))


# ==========================
# Toggle Complete
# ==========================

@app.route("/toggle/<int:id>")
def toggle(id):

    cursor.execute(
        "UPDATE tasks SET status = NOT status WHERE id=%s",
        (id,)
    )

    db.commit()

    return redirect(url_for("home"))


# ==========================
# Edit Task
# ==========================

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    if request.method == "POST":

        title = request.form.get("task")
        priority = request.form.get("priority")
        due_date = request.form.get("due_date")

        cursor.execute(
            """
            UPDATE tasks
            SET title=%s,
                priority=%s,
                due_date=%s
            WHERE id=%s
            """,
            (
                title.strip(),
                priority,
                due_date if due_date else None,
                id
            )
        )

        db.commit()

        return redirect(url_for("home"))

    cursor.execute(
        "SELECT * FROM tasks WHERE id=%s",
        (id,)
    )

    task = cursor.fetchone()

    if not task:
        return redirect(url_for("home"))

    return render_template(
        "edit.html",
        task=task
    )


# ==========================
# Run Application
# ==========================

if __name__ == "__main__":
    app.run(debug=True)