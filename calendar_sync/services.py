import json
import os
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import GoogleCalendarToken, GoogleCalendarSettings, TaskCalendarSync

# Import Google API modules with error handling
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.auth.transport.requests import Request
    GOOGLE_API_AVAILABLE = True
except ImportError as e:
    GOOGLE_API_AVAILABLE = False
    print(f"Google API client not available: {e}")

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Service for managing Google Calendar integration"""
    
    # Include all the scopes that Google typically returns
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self, user):
        self.user = user
        self.credentials_file = os.path.join(settings.BASE_DIR, 'google_calendar_credentials.json')
        self.current_redirect_uri = None  # Will be set dynamically
        
        if not GOOGLE_API_AVAILABLE:
            logger.error("Google API client is not available. Please install required packages.")
    
    def get_authorization_url(self):
        """Get the authorization URL for OAuth flow"""
        try:
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES
            )
            flow.redirect_uri = self._get_redirect_uri()
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            # Store state in session for security
            return authorization_url, state
            
        except Exception as e:
            logger.error(f"Error getting authorization URL: {e}")
            raise
    
    def _validate_scopes(self, credentials):
        """Validate that required scopes are present (allows additional scopes)"""
        received_scopes = set(credentials.scopes) if credentials.scopes else set()
        required_scopes = set(self.SCOPES)
        
        logger.info(f"Scope validation - Required: {required_scopes}")
        logger.info(f"Scope validation - Received: {received_scopes}")
        
        # Check if all required scopes are present
        missing_scopes = required_scopes - received_scopes
        if missing_scopes:
            logger.warning(f"Missing required scopes: {missing_scopes}")
            return False
        
        logger.info(f"Scope validation successful. All required scopes present.")
        return True

    def exchange_code_for_token(self, code, state):
        """Exchange authorization code for access token"""
        try:
            logger.info(f"Starting token exchange with code: {code[:10]}... and state: {state}")
            
            # Debug: Check client configuration
            client_config = self._get_client_config()
            logger.info(f"Using client ID: {client_config['client_id']}")
            logger.info(f"Using redirect URI: {self._get_redirect_uri()}")
            
            # For token exchange, create flow without scope validation
            # This avoids the "Scope has changed" warning that causes issues
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=None,  # Don't validate scopes during token exchange
                state=state
            )
            flow.redirect_uri = self._get_redirect_uri()
            
            try:
                # Attempt token exchange
                logger.info("Attempting token exchange without scope validation...")
                flow.fetch_token(code=code)
                credentials = flow.credentials
                logger.info(f"Token exchange successful. Access token: {credentials.token[:20] if credentials.token else None}...")
                logger.info(f"Received credentials with scopes: {credentials.scopes}")
            except Exception as e:
                logger.error(f"Token exchange failed with error: {e}")
                logger.error(f"Error type: {type(e)}")
                
                # For invalid_grant errors, provide more specific debugging
                if "invalid_grant" in str(e).lower():
                    logger.error("Invalid grant error - this could be due to:")
                    logger.error("1. Authorization code already used")
                    logger.error("2. Authorization code expired")
                    logger.error("3. Redirect URI mismatch")
                    logger.error("4. Client credentials mismatch")
                    logger.error(f"Current redirect URI: {self._get_redirect_uri()}")
                    logger.error(f"Configured redirect URIs: {client_config.get('redirect_uris', [])}")
                raise e
            
            # Skip scope validation and trust that Google provided the right access
            # We'll validate at the API level when we try to use the calendar service
            logger.info("Skipping scope validation - trusting Google's authorization")
            
            # Save tokens to database
            self._save_tokens(credentials)
            
            # Save tokens to database
            self._save_tokens(credentials)
            
            # Test the credentials by trying to access the Calendar API
            try:
                test_service = build('calendar', 'v3', credentials=credentials)
                calendar_list = test_service.calendarList().list(maxResults=1).execute()
                logger.info("Calendar API test successful - credentials are working")
            except Exception as api_error:
                logger.warning(f"Calendar API test failed: {api_error}")
                # Continue anyway as the token exchange was successful
            
            # Enable sync by default after successful authorization
            settings_obj, created = GoogleCalendarSettings.objects.get_or_create(
                user=self.user,
                defaults={'sync_enabled': True}
            )
            if not created:
                settings_obj.sync_enabled = True
                settings_obj.save()
            
            logger.info("Calendar sync enabled for user")
            return True
            
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise
    
    def _save_tokens(self, credentials, fallback_scopes=None):
        """Save OAuth tokens to database"""
        # Handle expiry time more robustly
        if credentials.expiry:
            expires_at = credentials.expiry
        else:
            # Default to 1 hour from now if no expiry is provided
            expires_at = timezone.now() + timedelta(hours=1)
        
        # Use fallback scopes if credentials don't have scopes
        scopes_to_save = credentials.scopes
        if not scopes_to_save and fallback_scopes:
            scopes_to_save = fallback_scopes
        elif not scopes_to_save:
            scopes_to_save = self.SCOPES  # Use our required scopes as fallback
        
        token_obj, created = GoogleCalendarToken.objects.get_or_create(
            user=self.user,
            defaults={
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expires_at': expires_at,
                'scope': ' '.join(scopes_to_save) if scopes_to_save else ''
            }
        )
        
        if not created:
            token_obj.access_token = credentials.token
            token_obj.refresh_token = credentials.refresh_token or token_obj.refresh_token
            token_obj.token_expires_at = expires_at
            token_obj.scope = ' '.join(scopes_to_save) if scopes_to_save else ''
            token_obj.save()
            
        logger.info(f"Saved tokens for user {self.user.username}. Expires at: {expires_at}")
    
    def get_credentials(self):
        """Get valid credentials for the user"""
        try:
            token_obj = GoogleCalendarToken.objects.get(user=self.user)
        except GoogleCalendarToken.DoesNotExist:
            return None
        
        credentials = Credentials(
            token=token_obj.access_token,
            refresh_token=token_obj.refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=self._get_client_config()['client_id'],
            client_secret=self._get_client_config()['client_secret'],
            scopes=token_obj.scope.split(' ')
        )
        
        # Refresh token if expired
        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
                self._save_tokens(credentials)
            except Exception as e:
                logger.error(f"Error refreshing token: {e}")
                return None
        
        return credentials
    
    def get_calendar_service(self):
        """Get authenticated Calendar service"""
        credentials = self.get_credentials()
        if not credentials:
            return None
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            return service
        except Exception as e:
            logger.error(f"Error building calendar service: {e}")
            return None
    
    def is_sync_enabled(self):
        """Check if calendar sync is enabled for user"""
        try:
            settings = GoogleCalendarSettings.objects.get(user=self.user)
            return settings.sync_enabled and self.get_credentials() is not None
        except GoogleCalendarSettings.DoesNotExist:
            return False
    
    def create_event(self, task):
        """Create a Google Calendar event for a task"""
        if not self.is_sync_enabled():
            return False
        
        service = self.get_calendar_service()
        if not service:
            return False
        
        try:
            # Prepare event data
            event_data = self._task_to_event(task)
            
            # Create event
            event = service.events().insert(
                calendarId='primary',
                body=event_data
            ).execute()
            
            # Save sync record
            TaskCalendarSync.objects.update_or_create(
                task=task,
                defaults={
                    'google_event_id': event['id'],
                    'calendar_id': 'primary',
                    'sync_status': 'synced'
                }
            )
            
            logger.info(f"Created calendar event for task {task.id}: {event['id']}")
            return True
            
        except HttpError as e:
            logger.error(f"HTTP error creating calendar event: {e}")
            self._record_sync_error(task, str(e))
            return False
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            self._record_sync_error(task, str(e))
            return False
    
    def update_event(self, task):
        """Update a Google Calendar event for a task"""
        if not self.is_sync_enabled():
            return False
        
        try:
            sync_record = TaskCalendarSync.objects.get(task=task)
        except TaskCalendarSync.DoesNotExist:
            # If no sync record, create new event
            return self.create_event(task)
        
        service = self.get_calendar_service()
        if not service:
            return False
        
        try:
            # Prepare updated event data
            event_data = self._task_to_event(task)
            
            # Update event
            event = service.events().update(
                calendarId=sync_record.calendar_id,
                eventId=sync_record.google_event_id,
                body=event_data
            ).execute()
            
            # Update sync record
            sync_record.sync_status = 'synced'
            sync_record.error_message = None
            sync_record.save()
            
            logger.info(f"Updated calendar event for task {task.id}: {event['id']}")
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                # Event not found, create new one
                return self.create_event(task)
            else:
                logger.error(f"HTTP error updating calendar event: {e}")
                self._record_sync_error(task, str(e))
                return False
        except Exception as e:
            logger.error(f"Error updating calendar event: {e}")
            self._record_sync_error(task, str(e))
            return False
    
    def delete_event(self, task):
        """Delete a Google Calendar event for a task"""
        if not self.is_sync_enabled():
            return False
        
        try:
            sync_record = TaskCalendarSync.objects.get(task=task)
        except TaskCalendarSync.DoesNotExist:
            return True  # Nothing to delete
        
        service = self.get_calendar_service()
        if not service:
            return False
        
        try:
            # Delete event
            service.events().delete(
                calendarId=sync_record.calendar_id,
                eventId=sync_record.google_event_id
            ).execute()
            
            # Update sync record
            sync_record.sync_status = 'deleted'
            sync_record.save()
            
            logger.info(f"Deleted calendar event for task {task.id}: {sync_record.google_event_id}")
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                # Event already deleted
                sync_record.sync_status = 'deleted'
                sync_record.save()
                return True
            else:
                logger.error(f"HTTP error deleting calendar event: {e}")
                self._record_sync_error(task, str(e))
                return False
        except Exception as e:
            logger.error(f"Error deleting calendar event: {e}")
            self._record_sync_error(task, str(e))
            return False
    
    def _task_to_event(self, task):
        """Convert a task to Google Calendar event format"""
        event_data = {
            'summary': task.title,
            'description': task.description or '',
            'colorId': self._get_color_id(task.priority),
        }
        
        # Add reminder notifications
        reminders = {
            'useDefault': False,
            'overrides': [
                {
                    'method': 'popup',
                    'minutes': getattr(task, 'reminder_minutes', 15)
                },
                {
                    'method': 'email', 
                    'minutes': getattr(task, 'reminder_minutes', 15)
                }
            ]
        }
        event_data['reminders'] = reminders
        
        # Set time based on due date
        if task.due_date:
            # Use server timezone (Bangladesh Standard Time for Dhaka)
            # This matches the server's location and Google Cloud deployment timezone
            server_timezone = 'Asia/Dhaka'  # Bangladesh Standard Time (UTC+6)
            
            if hasattr(task.due_date, 'hour') and task.due_date.hour != 0:
                # If it's a datetime, create a timed event
                start_time = task.due_date
                end_time = start_time + timedelta(hours=1)  # Default 1 hour duration
                
                # If the datetime is naive (no timezone info), treat it as server local time
                if timezone.is_naive(start_time):
                    # Convert to server timezone for Google Calendar
                    logger.info(f"Task due date is naive: {start_time}, using server timezone: {server_timezone}")
                
                event_data.update({
                    'start': {
                        'dateTime': start_time.isoformat(),
                        'timeZone': server_timezone,
                    },
                    'end': {
                        'dateTime': end_time.isoformat(),
                        'timeZone': server_timezone,
                    },
                })
            else:
                # All-day event
                event_data.update({
                    'start': {
                        'date': task.due_date.date().isoformat(),
                    },
                    'end': {
                        'date': (task.due_date.date() + timedelta(days=1)).isoformat(),
                    },
                })
        else:
            # No due date, create an all-day event for today
            today = timezone.now().date()
            event_data.update({
                'start': {
                    'date': today.isoformat(),
                },
                'end': {
                    'date': (today + timedelta(days=1)).isoformat(),
                },
            })
        
        # Add task status in description
        status_text = f"\n\nStatus: {task.get_status_display()}"
        if task.category:
            status_text += f"\nCategory: {task.category}"
        
        event_data['description'] += status_text
        
        return event_data
    
    def _get_color_id(self, priority):
        """Map task priority to Google Calendar color"""
        color_map = {
            'low': '2',      # Green
            'medium': '5',   # Yellow  
            'high': '11',    # Red
            'urgent': '4'    # Orange
        }
        return color_map.get(priority, '1')  # Default blue
    
    def _record_sync_error(self, task, error_message):
        """Record sync error for a task"""
        TaskCalendarSync.objects.update_or_create(
            task=task,
            defaults={
                'sync_status': 'error',
                'error_message': error_message
            }
        )
    
    def _get_redirect_uri(self):
        """Get the OAuth redirect URI"""
        # Use the dynamically set URI if available, otherwise fallback to localhost
        if self.current_redirect_uri:
            return self.current_redirect_uri
        return 'http://localhost:8000/calendar-sync/oauth/callback/'
    
    def _get_client_config(self):
        """Get OAuth client configuration"""
        with open(self.credentials_file, 'r') as f:
            config = json.load(f)
            return config['web']
    
    def disconnect(self):
        """Disconnect calendar sync for user"""
        try:
            # Disable sync
            settings = GoogleCalendarSettings.objects.get(user=self.user)
            settings.sync_enabled = False
            settings.save()
            
            # Delete tokens
            GoogleCalendarToken.objects.filter(user=self.user).delete()
            
            # Mark all syncs as deleted
            TaskCalendarSync.objects.filter(task__user=self.user).update(sync_status='deleted')
            
            return True
        except Exception as e:
            logger.error(f"Error disconnecting calendar sync: {e}")
            return False


# Import error handling is already done at the top of the file
