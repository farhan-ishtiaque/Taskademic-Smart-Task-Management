#!/usr/bin/env python
import os
import sys
import django
import requests
from bs4 import BeautifulSoup

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

def test_browser_session():
    """Test the analytics API with a real browser-like session"""
    print("🌐 Testing browser-like session...")
    
    # Create a session
    session = requests.Session()
    base_url = 'http://127.0.0.1:8000'
    
    # Step 1: Get the login page to obtain CSRF token
    print("📥 Getting login page...")
    login_url = f"{base_url}/accounts/login/"
    response = session.get(login_url)
    
    if response.status_code != 200:
        print(f"❌ Failed to get login page: {response.status_code}")
        return
    
    # Parse the CSRF token
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
    print(f"🔑 Got CSRF token: {csrf_token[:20]}...")
    
    # Step 2: Log in
    print("🔐 Logging in...")
    login_data = {
        'username': 'demo',
        'password': 'demo123',
        'csrfmiddlewaretoken': csrf_token
    }
    
    response = session.post(login_url, data=login_data)
    print(f"📊 Login response: {response.status_code}")
    
    # Check if redirected (successful login)
    if response.url != login_url:
        print(f"✅ Login successful! Redirected to: {response.url}")
    else:
        print("❌ Login may have failed")
        print(f"Response text: {response.text[:200]}...")
        return
    
    # Step 3: Test analytics API
    print("📈 Testing analytics API...")
    api_url = f"{base_url}/analytics/api/"
    response = session.get(api_url)
    print(f"📊 Analytics API response: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"✅ API Success! Data keys: {list(data.keys())}")
            print(f"📊 Overview: {data.get('overview', {})}")
        except Exception as e:
            print(f"❌ JSON parse error: {e}")
            print(f"Response text: {response.text[:200]}...")
    else:
        print(f"❌ API failed: {response.status_code}")
        print(f"Response text: {response.text[:200]}...")
    
    # Step 4: Test analytics dashboard page
    print("📊 Testing analytics dashboard...")
    dashboard_url = f"{base_url}/analytics/"
    response = session.get(dashboard_url)
    print(f"📈 Dashboard response: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Dashboard accessible!")
    else:
        print(f"❌ Dashboard failed: {response.status_code}")

if __name__ == '__main__':
    test_browser_session()
