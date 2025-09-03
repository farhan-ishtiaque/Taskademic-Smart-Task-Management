import os
import json
import logging
from django.conf import settings
import firebase_admin
from firebase_admin import credentials, auth

logger = logging.getLogger(__name__)

def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials"""
    
    if firebase_admin._apps:
        logger.info("Firebase already initialized")
        return True
    
    try:
        # Try to get credentials from environment variable (JSON string)
        service_account_info = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
        if service_account_info:
            try:
                service_account_dict = json.loads(service_account_info)
                cred = credentials.Certificate(service_account_dict)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized successfully from environment JSON")
                return True
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
        
        # Try to get credentials from file path
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
            logger.info(f"Firebase initialized successfully from file: {credentials_path}")
            return True
        
        # Try default credentials file in project
        default_path = os.path.join(settings.BASE_DIR, 'firebase-service-account.json')
        if os.path.exists(default_path):
            cred = credentials.Certificate(default_path)
            firebase_admin.initialize_app(cred)
            logger.info(f"Firebase initialized successfully from default path: {default_path}")
            return True
            
        logger.warning("No Firebase credentials found. Please set FIREBASE_SERVICE_ACCOUNT_JSON environment variable or place firebase-service-account.json in project root")
        return False
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return False

def verify_firebase_token(id_token):
    """Verify Firebase ID token and return decoded token"""
    try:
        if not firebase_admin._apps:
            if not initialize_firebase():
                raise Exception("Firebase not initialized")
        
        decoded_token = auth.verify_id_token(id_token)
        logger.info(f"Token verified successfully for user: {decoded_token.get('email')}")
        return decoded_token
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise