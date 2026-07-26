from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="78103609210380",      # Agar password hai to yahan likho
    database="taskflow_ai"
)

cursor = db.cursor()


@app.route("/")
def home():
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    return render_template("index.html", tasks=tasks)


@app.route("/add", methods=["POST"])
def add():
    task = request.form.get("task")

    if task and task.strip():
        sql = "INSERT INTO tasks (title) VALUES (%s)"
        values = (task.strip(),)

        cursor.execute(sql, values)
        db.commit()

    return redirect(url_for("home"))

# ==========================
# Delete Task
# ==========================

@app.route("/delete/<int:id>")
def delete(id):

    cursor.execute("DELETE FROM tasks WHERE id=%s", (id,))
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

    return render_template(
        "edit.html",
        task=task
    )


# ==========================
# Run Application
# ==========================

if __name__ == "__main__":
    app.run(debug=True)
