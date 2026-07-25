from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# MySQL Connection with error handling
def get_db_connection():
    try:
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "taskflow_ai")
        )
        return db
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Initialize database connection
db = get_db_connection()
if db:
    cursor = db.cursor()
else:
    print("Failed to connect to database")
    cursor = None


@app.route("/")
def home():
    try:
        if not cursor:
            return "Database connection error", 500
        cursor.execute("SELECT * FROM tasks")
        tasks = cursor.fetchall()
        return render_template("index.html", tasks=tasks)
    except Error as e:
        print(f"Error fetching tasks: {e}")
        return "Error fetching tasks", 500


@app.route("/add", methods=["POST"])
def add():
    try:
        task = request.form.get("task")

        if task and task.strip():
            sql = "INSERT INTO tasks (title) VALUES (%s)"
            values = (task.strip(),)

            cursor.execute(sql, values)
            db.commit()
    except Error as e:
        print(f"Error adding task: {e}")
        db.rollback()
    
    return redirect(url_for("home"))


@app.route("/delete/<int:id>")
def delete(id):
    try:
        cursor.execute("DELETE FROM tasks WHERE id=%s", (id,))
        db.commit()
    except Error as e:
        print(f"Error deleting task: {e}")
        db.rollback()

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
