from app import app
from flask import render_template

with app.test_request_context('/'):
    tasks = [{'id': 1, 'title': 'Sample Task', 'status': 0, 'priority': 'Medium', 'due_date': None}]
    print('type', type(tasks), 'len', len(tasks), 'bool', bool(tasks))
    html = render_template(
        'index.html',
        tasks=tasks,
        total=1,
        completed=0,
        pending=1,
        progress=0,
        high_priority=0,
        due_today=0,
        overdue=0,
        search='',
        filter_by='',
        sort_by='newest',
        today='2026-08-04'
    )
    print('contains sample', 'Sample Task' in html)
    print('contains task-card', 'task-card' in html)
