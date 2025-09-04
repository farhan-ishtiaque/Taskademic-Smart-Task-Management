#!/usr/bin/env python
"""
Test script to verify Google Calendar deletion functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

from django.contrib.auth.models import User
from tasks.models import Task
from calendar_sync.models import TaskCalendarSync
from calendar_sync.services import GoogleCalendarService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_calendar_deletion():
    """Test Google Calendar deletion functionality"""
    
    print("🧪 Testing Google Calendar Task Deletion")
    print("=" * 50)
    
    # Find a user with calendar sync enabled
    users_with_tasks = User.objects.filter(owned_tasks__isnull=False).distinct()
    
    if not users_with_tasks.exists():
        print("❌ No users with tasks found")
        return
    
    test_user = users_with_tasks.first()
    print(f"📋 Testing with user: {test_user.username}")
    
    # Check if user has calendar sync set up
    calendar_service = GoogleCalendarService(test_user)
    sync_enabled = calendar_service.is_sync_enabled()
    print(f"📅 Calendar sync enabled: {sync_enabled}")
    
    # Get tasks with calendar sync records
    synced_tasks = Task.objects.filter(
        user=test_user,
        calendar_syncs__isnull=False
    ).distinct()
    
    print(f"🔗 Tasks with calendar sync: {synced_tasks.count()}")
    
    if synced_tasks.exists():
        for task in synced_tasks[:3]:  # Test up to 3 tasks
            sync_records = TaskCalendarSync.objects.filter(task=task)
            print(f"  • Task: {task.title}")
            print(f"    Sync records: {sync_records.count()}")
            for record in sync_records:
                print(f"    - Calendar ID: {record.calendar_id}")
                print(f"    - Event ID: {record.google_event_id}")
                print(f"    - Status: {record.sync_status}")
    
    # Test the delete_event method without actually deleting
    if synced_tasks.exists():
        test_task = synced_tasks.first()
        print(f"\n🧪 Testing delete_event method for task: {test_task.title}")
        
        # Check if task has sync record
        try:
            sync_record = TaskCalendarSync.objects.get(task=test_task)
            print(f"✅ Found sync record: {sync_record.google_event_id}")
            
            if sync_enabled:
                print("⚠️  Would delete from Google Calendar (test mode)")
                # In a real test, you would call:
                # success = calendar_service.delete_event(test_task)
                # print(f"Deletion success: {success}")
            else:
                print("ℹ️  Calendar sync not enabled, would skip deletion")
                
        except TaskCalendarSync.DoesNotExist:
            print("ℹ️  No sync record found, nothing to delete")
    
    print("\n✅ Test completed!")
    print("\nTo fully test deletion:")
    print("1. Create a test task")
    print("2. Sync it to Google Calendar")
    print("3. Delete the task via Django")
    print("4. Verify it's removed from Google Calendar")


if __name__ == '__main__':
    test_calendar_deletion()
