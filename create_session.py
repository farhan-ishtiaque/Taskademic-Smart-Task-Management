#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.auth import login
from django.test import RequestFactory
from django.contrib.sessions.backends.db import SessionStore

def create_browser_session():
    """Create a session for the demo user that can be used in browser"""
    print("🔍 Creating browser session for demo user...")
    
    # Get demo user
    try:
        demo_user = User.objects.get(username='demo')
        print(f"✅ Found user: {demo_user.username}")
    except User.DoesNotExist:
        print("❌ Demo user not found")
        return
    
    # Create a session
    session = SessionStore()
    session['_auth_user_id'] = str(demo_user.id)
    session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
    session['_auth_user_hash'] = demo_user.get_session_auth_hash()
    session.save()
    
    print(f"✅ Session created: {session.session_key}")
    print(f"🌐 To use this session, set the sessionid cookie to: {session.session_key}")
    print(f"📱 Or you can manually log in with username: demo, password: demo123")

if __name__ == '__main__':
    create_browser_session()
