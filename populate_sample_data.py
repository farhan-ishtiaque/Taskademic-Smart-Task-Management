#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

from django.contrib.auth.models import User
from tasks.models import Task, Category
from datetime import datetime, timedelta

def populate_sample_data():
    # Get the admin user
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        print("Admin user not found. Creating one...")
        admin_user = User.objects.create_user('admin', 'admin@example.com', 'admin123')
    
    # Create additional users
    user2, created = User.objects.get_or_create(
        username='john_doe',
        defaults={
            'email': 'john@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }
    )
    if created:
        user2.set_password('password123')
        user2.save()
    
    user3, created = User.objects.get_or_create(
        username='jane_smith',
        defaults={
            'email': 'jane@example.com',
            'first_name': 'Jane',
            'last_name': 'Smith'
        }
    )
    if created:
        user3.set_password('password123')
        user3.save()
    
    # Create categories
    category1, created = Category.objects.get_or_create(
        name='Development',
        user=admin_user,
        defaults={'color': '#3B82F6'}
    )
    
    category2, created = Category.objects.get_or_create(
        name='Design',
        user=admin_user,
        defaults={'color': '#EC4899'}
    )
    
    category3, created = Category.objects.get_or_create(
        name='General',
        user=admin_user,
        defaults={'color': '#10B981'}
    )
    
    # Create simple tasks for individual users
    task_data = [
        {
            'title': 'Setup Development Environment',
            'description': 'Configure local development environment with all necessary tools',
            'user': admin_user,
            'category': category1,
            'priority': 'high',
            'status': 'in_progress',
            'due_date': datetime.now() + timedelta(days=2)
        },
        {
            'title': 'Complete project proposal',
            'description': 'Finish the Q4 project proposal and submit to management',
            'user': admin_user,
            'category': category3,
            'priority': 'urgent',
            'status': 'todo',
            'due_date': datetime.now() + timedelta(days=5)
        },
        {
            'title': 'Review code documentation',
            'description': 'Review and update existing code documentation for clarity',
            'user': user2,
            'category': category1,
            'priority': 'medium',
            'status': 'todo',
            'due_date': datetime.now() + timedelta(days=7)
        },
        {
            'title': 'Create UI mockups',
            'description': 'Design modern and responsive UI mockups for the dashboard',
            'user': user3,
            'category': category2,
            'priority': 'medium',
            'status': 'todo',
            'due_date': datetime.now() + timedelta(days=10)
        },
        {
            'title': 'Update personal portfolio',
            'description': 'Add recent projects to personal portfolio website',
            'user': user2,
            'category': category2,
            'priority': 'low',
            'status': 'done',
            'due_date': datetime.now() - timedelta(days=2)
        },
        {
            'title': 'Learn new framework',
            'description': 'Study and practice with the latest web development framework',
            'user': user3,
            'category': category1,
            'priority': 'low',
            'status': 'in_progress',
            'due_date': datetime.now() + timedelta(days=14)
        }
    ]
    
    for task_info in task_data:
        task, created = Task.objects.get_or_create(
            title=task_info['title'],
            user=task_info['user'],
            defaults=task_info
        )
        if created:
            print(f"Created task: {task.title}")
    
    print("Sample data populated successfully!")
    print(f"Categories created: {Category.objects.count()}")
    print(f"Tasks created: {Task.objects.count()}")

if __name__ == '__main__':
    populate_sample_data()
