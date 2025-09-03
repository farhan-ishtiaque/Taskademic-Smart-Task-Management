#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

from django.contrib.auth.models import User
from tasks.models import Task

print(f"Users: {User.objects.count()}")
for user in User.objects.all():
    print(f"- {user.username} ({user.email})")

print(f"\nTasks: {Task.objects.count()}")
for task in Task.objects.all()[:3]:
    print(f"- {task.title} (due: {task.due_date}) by {task.user.username}")

# Check if there are tasks with due dates
tasks_with_due_dates = Task.objects.filter(due_date__isnull=False)
print(f"\nTasks with due dates: {tasks_with_due_dates.count()}")
