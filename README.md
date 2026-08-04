# 🚀 TaskFlow-AI

TaskFlow-AI is a smart task management web application built with Python, Flask, and MySQL. It helps users manage tasks efficiently with features like search, filter, sorting, priority, due dates, flash messages, and progress tracking.

## ✨ Features

- Add tasks
- Edit tasks
- Delete tasks
- Mark tasks as completed
- Search tasks
- Filter tasks by status and priority
- Sort tasks by newest, oldest, priority, and due date
- Priority labels
- Due date tracking
- Overdue and due-today indicators
- Flash messages for user actions
- Responsive dashboard UI
- Progress bar
- AI task generation from a goal
- AI answers about pending, completed, overdue, and high-priority tasks

## 🛠 Tech Stack

- Python
- Flask
- MySQL
- HTML
- CSS
- JavaScript

## 📁 Project Structure

   text
TaskFlow-AI/
├── app.py
├── requirements.txt
├── .gitignore
├── templates/
│   ├── index.html
│   └── edit.html
├── static/
│   └── style.css
├── ai.py
├── README.md

## ▶️ Run the app

1. Install dependencies:
   pip install -r requirements.txt
2. Start the Flask app:
   python app.py
3. Open http://127.0.0.1:5000/

> Make sure your MySQL database is available and the environment variables for the database and Gemini API are set.
