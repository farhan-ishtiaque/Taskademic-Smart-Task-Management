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
from notifications.models import Notification, NotificationPreferences

User = get_user_model()

def create_team_task_notification_manually():
    """Manually create a team task notification to test the logic"""
    
    # Find a team with tasks
    teams_with_tasks = Team.objects.filter(tasks__isnull=False).distinct()
    
    if not teams_with_tasks.exists():
        print("No teams with tasks found")
        return
    
    team = teams_with_tasks.first()
    task = Task.objects.filter(team=team).first()
    
    print(f"Team: {team.name}")
    print(f"Task: {task.title}")
    print(f"Team members: {[m.username for m in team.members.all()]}")
    
    # Simulate a user moving the task
    moved_by_user = team.members.first()  # Use first team member as the mover
    old_status = 'todo'
    new_status = 'in_progress'
    
    # Get team members except the one who moved it
    team_members = team.members.exclude(id=moved_by_user.id)
    print(f"Will notify: {[m.username for m in team_members]}")
    
    # Status display mapping
    status_display = {
        'todo': 'To Do',
        'in_progress': 'In Progress',
        'review': 'Review',
        'done': 'Done'
    }
    
    old_status_display = status_display.get(old_status, old_status.title())
    new_status_display = status_display.get(new_status, new_status.title())
    
    # Count before
    before_count = Notification.objects.filter(notification_type='team_task_update').count()
    print(f"Notifications before: {before_count}")
    
    # Create notifications for each team member
    for member in team_members:
        # Check if user has team update notifications enabled
        try:
            preferences = NotificationPreferences.objects.get(user=member)
            if not preferences.team_updates:
                print(f"Skipping {member.username} - team updates disabled")
                continue
        except NotificationPreferences.DoesNotExist:
            print(f"Creating notification for {member.username} - no preferences (default enabled)")
        
        # Create notification
        notification = Notification.objects.create(
            user=member,
            title=f'Team Task Moved: {task.title}',
            message=f'{moved_by_user.get_full_name() or moved_by_user.username} moved "{task.title}" from {old_status_display} to {new_status_display}.',
            notification_type='team_task_update',
            team_id=task.team.id if task.team else None,
            is_read=False
        )
        print(f"Created notification {notification.id} for {member.username}")
    
    # Count after
    after_count = Notification.objects.filter(notification_type='team_task_update').count()
    print(f"Notifications after: {after_count}")
    print(f"New notifications created: {after_count - before_count}")

if __name__ == "__main__":
    create_team_task_notification_manually()
