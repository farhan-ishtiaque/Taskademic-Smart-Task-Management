#!/usr/bin/env python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')

import django
django.setup()

from tasks.models import Task
from teams.models import Team
from django.contrib.auth.models import User

# Check teams
teams = Team.objects.all()
print('Teams:', [(t.id, t.name) for t in teams])

# Check users  
users = User.objects.all()
print('Users:', [(u.id, u.username) for u in users])

# Check tasks with assignments
tasks = Task.objects.all()
for task in tasks:
    assigned_to = task.assigned_to.username if task.assigned_to else "None"
    team = task.team.name if hasattr(task, 'team') and task.team else "None"
    print(f'Task {task.id}: {task.title} - Assigned to: {assigned_to} - Team: {team}')
