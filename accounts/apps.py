from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        # Initialize Firebase when Django starts
        try:
            from taskademic.firebase_init import initialize_firebase
            initialize_firebase()
        except Exception as e:
            # Don't break Django startup if Firebase initialization fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Firebase initialization failed: {e}")
            pass
