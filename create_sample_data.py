#!/usr/bin/env python
"""
Sample data creation script for TaskAdemic
Run this after migrations to populate the database with test data.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

from django.contrib.auth.models import User
from tasks.models import Task, TimeBlock
from accounts.models import UserProfile


def create_sample_users():
    """Create sample users"""
    print("Creating sample users...")
    
    # Create test user if doesn't exist
    if not User.objects.filter(username='testuser').exists():
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print(f"Created user: {user.username}")
    else:
        user = User.objects.get(username='testuser')
        print(f"User already exists: {user.username}")
    
    # Update user profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    if created or profile.total_points == 0:
        profile.total_points = 50
        profile.level = 1
        profile.preferred_technique = 'pomodoro'
        profile.study_hours_per_day = 6
        profile.streak_count = 3
        profile.save()
        print(f"Updated profile for {user.username}")
    
    return user


def create_sample_tasks(user):
    """Create sample tasks for testing"""
    print("Creating sample tasks...")
    
    # Delete existing tasks for clean slate
    Task.objects.filter(user=user).delete()
    
    sample_tasks = [
        {
            'title': 'Complete Python Assignment',
            'description': 'Finish the data structures assignment for CS 101',
            'due_date': timezone.now() + timedelta(days=3),
            'estimated_duration': 120,
            'priority': 'must',
            'category': 'academic',
            'tags': 'python, assignment, cs101',
            'status': 'todo'
        },
        {
            'title': 'Study for Math Exam',
            'description': 'Review calculus chapters 5-8',
            'due_date': timezone.now() + timedelta(days=5),
            'estimated_duration': 180,
            'priority': 'must',
            'category': 'academic',
            'tags': 'math, calculus, exam',
            'status': 'in_progress'
        },
        {
            'title': 'Group Project Meeting',
            'description': 'Discuss final presentation with team members',
            'due_date': timezone.now() + timedelta(days=1),
            'estimated_duration': 60,
            'priority': 'should',
            'category': 'academic',
            'tags': 'meeting, project, teamwork',
            'status': 'todo'
        },
        {
            'title': 'Read Research Paper',
            'description': 'Read "Machine Learning in Healthcare" paper',
            'due_date': timezone.now() + timedelta(days=7),
            'estimated_duration': 90,
            'priority': 'could',
            'category': 'academic',
            'tags': 'research, ml, healthcare',
            'status': 'todo'
        },
        {
            'title': 'Complete Physics Lab Report',
            'description': 'Write up results from last weeks experiment',
            'due_date': timezone.now() - timedelta(days=1),  # Overdue
            'estimated_duration': 150,
            'priority': 'must',
            'category': 'academic',
            'tags': 'physics, lab, report',
            'status': 'todo'
        },
        {
            'title': 'Exercise - Gym Session',
            'description': 'Cardio and strength training',
            'due_date': timezone.now() + timedelta(days=1),
            'estimated_duration': 60,
            'priority': 'should',
            'category': 'personal',
            'tags': 'health, fitness, gym',
            'status': 'todo'
        },
        {
            'title': 'Call Parents',
            'description': 'Weekly check-in call with family',
            'due_date': timezone.now() + timedelta(days=2),
            'estimated_duration': 30,
            'priority': 'should',
            'category': 'personal',
            'tags': 'family, call',
            'status': 'todo'
        },
        {
            'title': 'Grocery Shopping',
            'description': 'Buy groceries for the week',
            'due_date': timezone.now() + timedelta(days=2),
            'estimated_duration': 45,
            'priority': 'could',
            'category': 'personal',
            'tags': 'shopping, groceries',
            'status': 'todo'
        },
        {
            'title': 'Fix Laptop Issue',
            'description': 'Troubleshoot slow performance issue',
            'due_date': timezone.now() + timedelta(hours=6),
            'estimated_duration': 120,
            'priority': 'must',
            'category': 'urgent',
            'tags': 'laptop, tech, urgent',
            'status': 'todo'
        },
        {
            'title': 'Submit Scholarship Application',
            'description': 'Complete and submit scholarship application',
            'due_date': timezone.now() + timedelta(hours=12),
            'estimated_duration': 180,
            'priority': 'must',
            'category': 'urgent',
            'tags': 'scholarship, application, deadline',
            'status': 'in_progress'
        },
        # Some completed tasks for analytics
        {
            'title': 'Chemistry Quiz',
            'description': 'Online chemistry quiz on organic compounds',
            'due_date': timezone.now() - timedelta(days=2),
            'estimated_duration': 45,
            'priority': 'must',
            'category': 'academic',
            'tags': 'chemistry, quiz, organic',
            'status': 'done',
            'completed_at': timezone.now() - timedelta(days=2),
            'points_awarded': 10
        },
        {
            'title': 'Weekly Meal Prep',
            'description': 'Prepare meals for the upcoming week',
            'due_date': timezone.now() - timedelta(days=3),
            'estimated_duration': 120,
            'priority': 'should',
            'category': 'personal',
            'tags': 'cooking, meal prep',
            'status': 'done',
            'completed_at': timezone.now() - timedelta(days=3),
            'points_awarded': 10
        },
        {
            'title': 'Library Book Return',
            'description': 'Return borrowed books to university library',
            'due_date': timezone.now() - timedelta(days=1),
            'estimated_duration': 20,
            'priority': 'should',
            'category': 'personal',
            'tags': 'library, books',
            'status': 'done',
            'completed_at': timezone.now() - timedelta(days=1),
            'points_awarded': 10
        }
    ]
    
    created_tasks = []
    for task_data in sample_tasks:
        task = Task.objects.create(user=user, **task_data)
        created_tasks.append(task)
        print(f"Created task: {task.title}")
    
    print(f"Created {len(created_tasks)} sample tasks")
    return created_tasks


def create_sample_time_blocks(user):
    """Create sample time blocks"""
    print("Creating sample time blocks...")
    
    # Delete existing time blocks
    TimeBlock.objects.filter(user=user).delete()
    
    # Create time blocks for each day of the week
    sample_blocks = [
        # Monday
        {'day_of_week': 0, 'start_time': '09:00', 'end_time': '11:00'},
        {'day_of_week': 0, 'start_time': '14:00', 'end_time': '16:00'},
        {'day_of_week': 0, 'start_time': '19:00', 'end_time': '21:00'},
        
        # Tuesday
        {'day_of_week': 1, 'start_time': '10:00', 'end_time': '12:00'},
        {'day_of_week': 1, 'start_time': '15:00', 'end_time': '17:00'},
        
        # Wednesday
        {'day_of_week': 2, 'start_time': '09:00', 'end_time': '11:00'},
        {'day_of_week': 2, 'start_time': '13:00', 'end_time': '15:00'},
        {'day_of_week': 2, 'start_time': '18:00', 'end_time': '20:00'},
        
        # Thursday
        {'day_of_week': 3, 'start_time': '11:00', 'end_time': '13:00'},
        {'day_of_week': 3, 'start_time': '16:00', 'end_time': '18:00'},
        
        # Friday
        {'day_of_week': 4, 'start_time': '09:00', 'end_time': '11:00'},
        {'day_of_week': 4, 'start_time': '14:00', 'end_time': '16:00'},
        
        # Weekend (lighter schedule)
        {'day_of_week': 5, 'start_time': '10:00', 'end_time': '12:00'},  # Saturday
        {'day_of_week': 6, 'start_time': '15:00', 'end_time': '17:00'},  # Sunday
    ]
    
    created_blocks = []
    for block_data in sample_blocks:
        block = TimeBlock.objects.create(user=user, **block_data)
        created_blocks.append(block)
    
    print(f"Created {len(created_blocks)} time blocks")
    return created_blocks


def main():
    """Main function to create all sample data"""
    print("=" * 50)
    print("Creating TaskAdemic Sample Data")
    print("=" * 50)
    
    try:
        # Create users
        user = create_sample_users()
        
        # Create tasks
        tasks = create_sample_tasks(user)
        
        # Create time blocks
        time_blocks = create_sample_time_blocks(user)
        
        print("\n" + "=" * 50)
        print("Sample Data Creation Complete!")
        print("=" * 50)
        print(f"Created:")
        print(f"  - 1 test user (username: testuser, password: testpass123)")
        print(f"  - {len(tasks)} sample tasks")
        print(f"  - {len(time_blocks)} time blocks")
        print("\nYou can now:")
        print("  1. Login with testuser/testpass123")
        print("  2. View the dashboard with sample data")
        print("  3. Test all features with realistic data")
        print("\n" + "=" * 50)
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
