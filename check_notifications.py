#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the path
sys.path.append('E:/Taskademic')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

from notifications.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

try:
    user = User.objects.get(username='farhan')
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    
    print(f"Total notifications for farhan: {notifications.count()}")
    print("\nNotifications:")
    for n in notifications[:5]:  # Show latest 5
        print(f"ID: {n.id}")
        print(f"Title: {n.title}")
        print(f"Message: {n.message}")
        print(f"Type: {n.notification_type}")
        print(f"Read: {n.is_read}")
        print(f"Created: {n.created_at}")
        print("-" * 50)
        
except User.DoesNotExist:
    print("User 'farhan' not found")
except Exception as e:
    print(f"Error: {e}")
