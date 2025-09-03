#!/usr/bin/env python
import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import connection

# Test our raw SQL query
user = User.objects.get(username='cgptplus27')
print(f"Testing calendar query for user: {user.username}")

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT id, title, description, due_date, priority, status 
        FROM tasks_task 
        WHERE user_id = %s AND due_date IS NOT NULL
        ORDER BY due_date
    """, [user.id])
    
    tasks = []
    for row in cursor.fetchall():
        tasks.append({
            'id': row[0],
            'title': row[1],
            'description': row[2] or '',
            'due_date': row[3].isoformat() if row[3] else None,
            'priority': row[4],
            'status': row[5],
            'category': 'work'  # Default category
        })
    
    print(f"Found {len(tasks)} tasks")
    for task in tasks[:3]:
        print(f"- {task['title']} (due: {task['due_date']})")
        
    # Test if user has tasks due today
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    today_tasks = [t for t in tasks if t['due_date'] and t['due_date'].startswith(today)]
    print(f"Tasks due today ({today}): {len(today_tasks)}")
    for task in today_tasks:
        print(f"  - {task['title']}")
