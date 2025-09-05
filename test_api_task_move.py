#!/usr/bin/env python
import os
import sys
import django
import requests
import json

# Add the project directory to the path
sys.path.append('E:/Taskademic')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

from tasks.models import Task
from teams.models import Team
from django.contrib.auth import get_user_model
from notifications.models import Notification, NotificationPreferences
from django.test import Client
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

def test_team_task_move_via_api():
    """Test team task move notification via API simulation"""
    
    # Find a team with tasks
    teams_with_tasks = Team.objects.filter(tasks__isnull=False).distinct()
    
    if not teams_with_tasks.exists():
        print("No teams with tasks found")
        return
    
    team = teams_with_tasks.first()
    task = Task.objects.filter(team=team).first()
    user = team.members.first()
    
    print(f"Team: {team.name}")
    print(f"Task: {task.title} (current status: {task.status})")
    print(f"Team members: {[m.username for m in team.members.all()]}")
    print(f"User moving task: {user.username}")
    
    # Enable team updates for all team members to test notifications
    for member in team.members.all():
        prefs, created = NotificationPreferences.objects.get_or_create(user=member)
        prefs.team_updates = True
        prefs.save()
        print(f"Enabled team updates for {member.username}")
    
    # Count notifications before
    before_count = Notification.objects.filter(notification_type='team_task_update').count()
    print(f"Team task notifications before: {before_count}")
    
    # Simulate the API call using Django's test client
    from django.test import Client
    from django.contrib.sessions.middleware import SessionMiddleware
    from django.contrib.auth.middleware import AuthenticationMiddleware
    
    # Create a test client and login
    client = Client()
    client.force_login(user)
    
    # Prepare the new status (cycle through statuses)
    status_cycle = ['todo', 'in_progress', 'review', 'done']
    current_index = status_cycle.index(task.status) if task.status in status_cycle else 0
    new_status = status_cycle[(current_index + 1) % len(status_cycle)]
    
    print(f"Changing status from {task.status} to {new_status}")
    
    # Make API call to update task status
    response = client.patch(
        f'/tasks/api/tasks/{task.id}/',
        data=json.dumps({'status': new_status}),
        content_type='application/json'
    )
    
    print(f"API Response Status: {response.status_code}")
    
    if response.status_code == 200:
        print("Task updated successfully")
        
        # Refresh task from DB
        task.refresh_from_db()
        print(f"New task status: {task.status}")
        
        # Count notifications after
        after_count = Notification.objects.filter(notification_type='team_task_update').count()
        print(f"Team task notifications after: {after_count}")
        print(f"New notifications created: {after_count - before_count}")
        
        # Show the latest team task notifications
        latest_notifications = Notification.objects.filter(
            notification_type='team_task_update'
        ).order_by('-created_at')[:3]
        
        print("\nLatest team task notifications:")
        for notif in latest_notifications:
            print(f"- {notif.user.username}: {notif.title}")
            print(f"  {notif.message}")
            print(f"  Created: {notif.created_at}")
            print()
    else:
        print(f"API call failed: {response.content}")

if __name__ == "__main__":
    test_team_task_move_via_api()
