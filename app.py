from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

tasks = []

@app.route("/")
def home():
    return render_template("index.html", tasks=tasks)


@app.route("/add", methods=["POST"])
def add():
    task = request.form.get("task")

    if task and task.strip():
        tasks.append(task.strip())

    return redirect(url_for("home"))


@app.route("/delete/<int:index>")
def delete(index):

    if 0 <= index < len(tasks):
        tasks.pop(index)

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)