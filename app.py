from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# ==========================
# MySQL Connection
# ==========================

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="78103609210380",      # <-- Apna MySQL password yahan likho
        database="taskflow_ai"
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

    cursor.execute("SELECT COUNT(*) AS completed FROM tasks WHERE status = 1")
    completed = cursor.fetchone()["completed"]

    pending = total - completed

    if total == 0:
        progress = 0
    else:
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

    if task and task.strip():

        cursor.execute(
            "INSERT INTO tasks(title) VALUES(%s)",
            (task.strip(),)
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
# Toggle Complete Task
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

        new_task = request.form.get("task")

        if new_task and new_task.strip():

            cursor.execute(
                "UPDATE tasks SET title=%s WHERE id=%s",
                (new_task.strip(), id)
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
# Run Flask App
# ==========================

if __name__ == "__main__":
    app.run(debug=True)