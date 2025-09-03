from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .services import GoogleCalendarService
from .models import GoogleCalendarSettings, TaskCalendarSync
import logging

logger = logging.getLogger(__name__)


@login_required
def calendar_settings(request):
    """Calendar sync settings page"""
    calendar_service = GoogleCalendarService(request.user)
    
    # Get user settings
    try:
        settings = GoogleCalendarSettings.objects.get(user=request.user)
    except GoogleCalendarSettings.DoesNotExist:
        settings = None
    
    # Check if user has valid credentials
    has_credentials = calendar_service.get_credentials() is not None
    
    context = {
        'settings': settings,
        'has_credentials': has_credentials,
        'sync_enabled': settings.sync_enabled if settings else False,
    }
    
    return render(request, 'calendar_sync/settings.html', context)


@login_required
def connect_calendar(request):
    """Initiate Google Calendar OAuth flow"""
    try:
        calendar_service = GoogleCalendarService(request.user)
        
        # Set the redirect URI based on the current request host
        host = request.get_host()
        redirect_uri = f"http://{host}/calendar-sync/oauth/callback/"
        
        logger.info(f"Request host: {host}")
        logger.info(f"Generated redirect URI: {redirect_uri}")
        
        # Store the redirect URI in the service for consistency
        calendar_service.current_redirect_uri = redirect_uri
        
        authorization_url, state = calendar_service.get_authorization_url()
        
        # Store state in session for security
        request.session['oauth_state'] = state
        
        logger.info(f"Generated OAuth state: {state}")
        logger.info(f"Authorization URL: {authorization_url}")
        logger.info(f"Initiating OAuth with redirect URI: {redirect_uri}")
        
        return redirect(authorization_url)
        
    except Exception as e:
        logger.error(f"Error initiating calendar connection: {e}")
        messages.error(request, 'Failed to connect to Google Calendar. Please try again.')
        return redirect('calendar_sync:settings')


@login_required
def oauth_callback(request):
    """Handle OAuth callback from Google"""
    logger.info(f"OAuth callback called for user: {request.user}")
    
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    scope = request.GET.get('scope', '')  # Get scope from callback
    
    logger.info(f"OAuth callback params - code: {code[:10] if code else None}..., state: {state}, error: {error}")
    logger.info(f"Scopes from Google callback: {scope}")
    
    if error:
        logger.error(f"OAuth error: {error}")
        messages.error(request, f'Google Calendar authorization failed: {error}')
        return redirect('calendar_sync:settings')
    
    if not code or not state:
        logger.error("Missing code or state in OAuth callback")
        messages.error(request, 'Invalid authorization response.')
        return redirect('calendar_sync:settings')
    
    # Verify state for security
    stored_state = request.session.get('oauth_state')
    logger.info(f"State verification - received: {state}, stored: {stored_state}")
    
    if state != stored_state:
        logger.error("State mismatch in OAuth callback")
        messages.error(request, 'Invalid authorization state.')
        return redirect('calendar_sync:settings')
    
    try:
        calendar_service = GoogleCalendarService(request.user)
        
        # Set the same redirect URI that was used for authorization
        host = request.get_host()
        redirect_uri = f"http://{host}/calendar-sync/oauth/callback/"
        calendar_service.current_redirect_uri = redirect_uri
        
        success = calendar_service.exchange_code_for_token(code, state)
        
        if success:
            logger.info("Calendar connection successful")
            messages.success(request, 'Google Calendar connected successfully! Sync has been enabled.')
        else:
            logger.error("Calendar connection failed")
            messages.error(request, 'Failed to connect Google Calendar.')
            
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        messages.error(request, 'Failed to connect Google Calendar. Please try again.')
    
    finally:
        # Clean up session
        request.session.pop('oauth_state', None)
    
    return redirect('calendar_sync:settings')


@login_required
@require_http_methods(["POST"])
def toggle_sync(request):
    """Toggle calendar sync on/off"""
    try:
        settings, created = GoogleCalendarSettings.objects.get_or_create(
            user=request.user,
            defaults={'sync_enabled': False}
        )
        
        # Check if user has credentials
        calendar_service = GoogleCalendarService(request.user)
        if not calendar_service.get_credentials():
            return JsonResponse({
                'success': False,
                'error': 'Please connect your Google Calendar first.'
            })
        
        # Toggle sync
        settings.sync_enabled = not settings.sync_enabled
        settings.save()
        
        return JsonResponse({
            'success': True,
            'sync_enabled': settings.sync_enabled,
            'message': f'Calendar sync {"enabled" if settings.sync_enabled else "disabled"}.'
        })
        
    except Exception as e:
        logger.error(f"Error toggling sync: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to update sync settings.'
        })


@login_required
@require_http_methods(["POST"])
def disconnect_calendar(request):
    """Disconnect Google Calendar"""
    try:
        calendar_service = GoogleCalendarService(request.user)
        success = calendar_service.disconnect()
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Google Calendar disconnected successfully.'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to disconnect Google Calendar.'
            })
            
    except Exception as e:
        logger.error(f"Error disconnecting calendar: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to disconnect Google Calendar.'
        })


@login_required
def sync_status(request):
    """Get calendar sync status for user's tasks"""
    try:
        # Get sync records for user's tasks
        sync_records = TaskCalendarSync.objects.filter(
            task__user=request.user
        ).select_related('task')
        
        sync_data = []
        for record in sync_records:
            sync_data.append({
                'task_id': record.task.id,
                'task_title': record.task.title,
                'google_event_id': record.google_event_id,
                'sync_status': record.sync_status,
                'last_synced': record.last_synced.isoformat() if record.last_synced else None,
                'error_message': record.error_message
            })
        
        return JsonResponse({
            'success': True,
            'sync_records': sync_data
        })
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get sync status.'
        })


@login_required
@require_http_methods(["POST"])
def force_sync_task(request, task_id):
    """Manually force sync a specific task"""
    try:
        from tasks.models import Task
        task = Task.objects.get(id=task_id, user=request.user)
        
        calendar_service = GoogleCalendarService(request.user)
        if not calendar_service.is_sync_enabled():
            return JsonResponse({
                'success': False,
                'error': 'Calendar sync is not enabled.'
            })
        
        # Force update/create the event
        success = calendar_service.update_event(task)
        
        return JsonResponse({
            'success': success,
            'message': 'Task synced successfully.' if success else 'Failed to sync task.'
        })
        
    except Task.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Task not found.'
        })
    except Exception as e:
        logger.error(f"Error force syncing task {task_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to sync task.'
        })
