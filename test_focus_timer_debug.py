#!/usr/bin/env python
"""
Test script to debug focus timer source parameter issue
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')

# Setup Django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from dashboard.models import ScheduledTask, DailySchedule
from datetime import date

def main():
    print("=== Focus Timer Debug Test ===")
    print()
    
    # Get the user with tasks
    task_owner = ScheduledTask.objects.filter(scheduled_date=date.today()).first()
    if not task_owner:
        print("❌ No scheduled tasks found for today")
        return
    
    user = task_owner.user
    print(f"Testing with user: {user.username}")
    
    # Get the schedule
    schedule = DailySchedule.objects.filter(user=user, date=date.today()).first()
    if schedule:
        print(f"Schedule generation_method: {schedule.generation_method}")
    else:
        print("❌ No schedule found")
        return
    
    # Test the exact URL that would be generated
    url = f"/dashboard/focus-timer/?source={schedule.generation_method}"
    print(f"Testing URL: {url}")
    
    client = Client()
    client.force_login(user)
    
    response = client.get(url)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode()
        
        # Check the source parameter in the context
        if 'source=ai' in url:
            if 'AI Generated Schedule</strong>' in content:
                print("✅ AI Schedule correctly displayed")
            elif 'Custom Schedule</strong>' in content:
                print("❌ AI Schedule showing as Custom!")
            else:
                print("? Unknown display mode")
        
        elif 'source=custom' in url:
            if 'Custom Schedule</strong>' in content:
                print("✅ Custom Schedule correctly displayed")
            elif 'AI Generated Schedule</strong>' in content:
                print("❌ Custom Schedule showing as AI!")
            else:
                print("? Unknown display mode")
    
    print()
    print("=== Manual URL Tests ===")
    
    # Test both source types manually
    test_urls = [
        "/dashboard/focus-timer/?source=ai",
        "/dashboard/focus-timer/?source=custom",
        "/dashboard/focus-timer/"
    ]
    
    for test_url in test_urls:
        print(f"Testing: {test_url}")
        response = client.get(test_url)
        if response.status_code == 200:
            content = response.content.decode()
            if 'AI Generated Schedule</strong>' in content:
                print("  → Shows: AI Generated Schedule")
            elif 'Custom Schedule</strong>' in content:
                print("  → Shows: Custom Schedule")
            elif 'All Tasks</strong>' in content:
                print("  → Shows: All Tasks")
            else:
                print("  → Shows: Unknown")
        else:
            print(f"  → Error: {response.status_code}")

if __name__ == "__main__":
    main()
