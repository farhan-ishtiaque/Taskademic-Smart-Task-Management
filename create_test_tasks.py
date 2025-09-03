#!/usr/bin/env python
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

from django.contrib.auth.models import User
from tasks.models import Task

# Get the test user
user = User.objects.get(username='testuser')

# Create tasks for different dates
today = datetime.now()

# Today's tasks
Task.objects.create(
    user=user,
    title="Today's Important Meeting",
    description="Weekly team meeting",
    due_date=today,
    category='work',
    priority='must'
)

# Tomorrow's tasks
tomorrow = today + timedelta(days=1)
Task.objects.create(
    user=user,
    title="Tomorrow's Workout",
    description="Go to the gym",
    due_date=tomorrow,
    category='health',
    priority='should'
)

# Next week's task
next_week = today + timedelta(days=7)
Task.objects.create(
    user=user,
    title="Study Session",
    description="Prepare for exam",
    due_date=next_week,
    category='study',
    priority='must'
)

print(f"Created 3 test tasks for user: {user.username}")
print(f"Tasks for testuser: {Task.objects.filter(user=user).count()}")
