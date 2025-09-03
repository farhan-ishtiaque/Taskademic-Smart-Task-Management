"""
Firebase Authentication Diagnostic Script
This script helps diagnose Firebase authentication issues
"""

import os
import json
import requests
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Diagnose Firebase authentication configuration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Firebase Authentication Diagnostics ===\n'))
        
        # Check Firebase service account
        service_account_path = 'firebase-service-account.json'
        if os.path.exists(service_account_path):
            with open(service_account_path, 'r') as f:
                service_account = json.load(f)
                self.stdout.write(f"✅ Service Account Project ID: {service_account.get('project_id')}")
                self.stdout.write(f"✅ Service Account Client ID: {service_account.get('client_id')}")
                self.stdout.write(f"✅ Service Account Email: {service_account.get('client_email')}")
        else:
            self.stdout.write(self.style.ERROR("❌ firebase-service-account.json not found"))
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("🔧 REQUIRED ACTIONS:")
        self.stdout.write("="*50)
        
        self.stdout.write("\n1. Go to Firebase Console:")
        self.stdout.write("   https://console.firebase.google.com/project/taskademic1/authentication/providers")
        
        self.stdout.write("\n2. Enable Google Sign-In provider:")
        self.stdout.write("   - Click on 'Google' provider")
        self.stdout.write("   - Enable it if not already enabled")
        self.stdout.write("   - Set Web SDK configuration:")
        self.stdout.write("     Web client ID: 67763949564-okb9vi2rgv0sftfqvdp17ujd68pngr6f.apps.googleusercontent.com")
        self.stdout.write("     Web client secret: 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")
        
        self.stdout.write("\n3. Add authorized domains:")
        self.stdout.write("   - 127.0.0.1")
        self.stdout.write("   - localhost")
        
        self.stdout.write("\n4. Verify your OAuth client in Google Console:")
        self.stdout.write("   https://console.cloud.google.com/apis/credentials")
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("🧪 TESTING CONFIGURATION:")
        self.stdout.write("="*50)
        
        # Test Firebase project configuration
        try:
            from taskademic.firebase_init import initialize_firebase
            if initialize_firebase():
                self.stdout.write("✅ Firebase Admin SDK initialized successfully")
            else:
                self.stdout.write("❌ Firebase Admin SDK initialization failed")
        except Exception as e:
            self.stdout.write(f"❌ Firebase Admin SDK error: {e}")
        
        self.stdout.write("\n📋 Next Steps:")
        self.stdout.write("1. Complete Firebase Console configuration above")
        self.stdout.write("2. Wait 5-10 minutes for changes to propagate")
        self.stdout.write("3. Test authentication at: http://127.0.0.1:8000/accounts/login/")
        self.stdout.write("4. Check browser console for any errors")
