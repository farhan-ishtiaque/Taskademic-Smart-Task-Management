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
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def test_dashboard_data():
    """Test dashboard data for a user"""
    
    # Find a user to test with
    users = User.objects.all()[:3]
    
    for user in users:
        print(f"\n=== Testing dashboard data for {user.username} ===")
        
        # Personal tasks (created by user, no team)
        user_tasks = Task.objects.filter(user=user, team__isnull=True)
        print(f"Personal tasks (created by user): {user_tasks.count()}")
        
        # Tasks assigned to user (both personal and team)
        assigned_tasks = Task.objects.filter(assigned_to=user)
        print(f"Tasks assigned to user: {assigned_tasks.count()}")
        if assigned_tasks.exists():
            for task in assigned_tasks[:3]:
                print(f"  - {task.title} (Team: {task.team.name if task.team else 'Personal'})")
        
        # Recent tasks (last 7 days)
        recent_tasks = Task.objects.filter(
            Q(user=user, team__isnull=True) | Q(assigned_to=user),
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:5]
        print(f"Recent tasks (last 7 days): {recent_tasks.count()}")
        
        # Upcoming tasks (next 7 days)
        upcoming_tasks = Task.objects.filter(
            Q(user=user, team__isnull=True) | Q(assigned_to=user),
            due_date__gte=timezone.now(),
            due_date__lte=timezone.now() + timedelta(days=7),
            status__in=['todo', 'in_progress']
        ).order_by('due_date')[:5]
        print(f"Upcoming tasks (next 7 days): {upcoming_tasks.count()}")
        if upcoming_tasks.exists():
            for task in upcoming_tasks:
                print(f"  - {task.title} (Due: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No date'})")
        
        # Overdue tasks
        overdue_tasks = Task.objects.filter(
            Q(user=user, team__isnull=True) | Q(assigned_to=user),
            due_date__lt=timezone.now(),
            status__in=['todo', 'in_progress']
        ).order_by('due_date')[:5]
        print(f"Overdue tasks: {overdue_tasks.count()}")
        if overdue_tasks.exists():
            for task in overdue_tasks:
                print(f"  - {task.title} (Due: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No date'})")
        
        # Task completion rate
        total_tasks = user_tasks.count()
        completed_tasks = user_tasks.filter(status='done').count()
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        print(f"Completion rate: {completion_rate:.1f}% ({completed_tasks}/{total_tasks})")

if __name__ == "__main__":
    test_dashboard_data()
