#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

def test_analytics_api():
    """Test analytics API with authenticated user"""
    print("🔍 Testing Analytics API...")
    
    # Create a test client
    client = Client()
    
    # Login with demo user
    user = User.objects.get(username='demo')
    client.force_login(user)
    print(f"✅ Logged in as: {user.username}")
    
    # Test analytics dashboard page with proper host header
    response = client.get('/analytics/', HTTP_HOST='127.0.0.1:8000')
    print(f"✅ Analytics dashboard: {response.status_code}")
    
    # Test analytics API with proper host header
    response = client.get('/analytics/api/', HTTP_HOST='127.0.0.1:8000')
    print(f"✅ Analytics API: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API returned: {list(data.keys())}")
        print(f"📊 Overview: {data.get('overview', {})}")
    else:
        print(f"❌ API error: {response.content.decode()[:200]}...")

if __name__ == '__main__':
    test_analytics_api()
