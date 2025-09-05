#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the path
sys.path.append('E:/Taskademic')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

from tasks.models import Task
from teams.models import Team
from django.contrib.auth import get_user_model
from notifications.models import Notification

User = get_user_model()

def test_team_task_notification():
    # Find a team with tasks
    teams_with_tasks = Team.objects.filter(tasks__isnull=False).distinct()
    
    if not teams_with_tasks.exists():
        print("No teams with tasks found")
        return
    
    team = teams_with_tasks.first()
    print(f"Testing with team: {team.name}")
    
    # Get team tasks (any status)
    team_tasks = Task.objects.filter(team=team)
    
    if not team_tasks.exists():
        print("No team tasks found")
        return
    
    task = team_tasks.first()
    print(f"Testing with task: {task.title}")
    print(f"Current status: {task.status}")
    print(f"Team members: {[m.username for m in team.members.all()]}")
    
    # Count current notifications
    before_count = Notification.objects.filter(notification_type='team_task_update').count()
    print(f"Notifications before: {before_count}")
    
    # Simulate status change (manually change status to test notification logic)
    old_status = task.status
    task.status = 'in_progress'
    task.save()
    
    print(f"Changed task status from {old_status} to {task.status}")
    
    # Count notifications after
    after_count = Notification.objects.filter(notification_type='team_task_update').count()
    print(f"Notifications after: {after_count}")
    print(f"New notifications created: {after_count - before_count}")
    
    # Show recent team task notifications
    recent_notifications = Notification.objects.filter(
        notification_type='team_task_update'
    ).order_by('-created_at')[:5]
    
    print("\nRecent team task notifications:")
    for notif in recent_notifications:
        print(f"- {notif.user.username}: {notif.title}")
        print(f"  Message: {notif.message}")
        print(f"  Created: {notif.created_at}")
        print()

if __name__ == "__main__":
    test_team_task_notification()
