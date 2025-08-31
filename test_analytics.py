#!/usr/bin/env python
"""
Test script to debug analytics API issues
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from tasks.models import Task, Category

def test_analytics_api():
    """Test the analytics API to debug loading issues"""
    print("🔍 Testing Analytics API...")
    
    # Create test client
    client = Client()
    
    # Try to get or create a test user
    try:
        user = User.objects.get(username='testuser')
        print(f"✅ Found test user: {user.username}")
    except User.DoesNotExist:
        try:
            user = User.objects.first()
            if not user:
                user = User.objects.create_user(
                    username='testuser',
                    email='test@example.com',
                    password='testpassword'
                )
            print(f"✅ Using user: {user.username}")
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return False
    
    # Login the user
    client.force_login(user)
    print("✅ User logged in")
    
    # Test analytics dashboard page
    try:
        response = client.get('/analytics/')
        print(f"✅ Analytics dashboard: {response.status_code}")
    except Exception as e:
        print(f"❌ Analytics dashboard error: {e}")
    
    # Test analytics API endpoint
    try:
        response = client.get('/analytics/api/')
        print(f"✅ Analytics API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response keys: {list(data.keys())}")
            if 'overview' in data:
                print(f"✅ Overview data: {data['overview']}")
        else:
            print(f"❌ API returned: {response.content}")
    except Exception as e:
        print(f"❌ Analytics API error: {e}")
    
    # Check if user has tasks
    task_count = Task.objects.filter(user=user).count()
    print(f"✅ User has {task_count} tasks")
    
    return True

if __name__ == '__main__':
    test_analytics_api()
