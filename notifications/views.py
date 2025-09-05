from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Notification, NotificationPreferences
from teams.models import TeamInvite, Team
import json


@login_required
def notification_list(request):
    """Display user's notifications"""
    notifications = request.user.notifications.all()[:20]  # Latest 20
    unread_count = request.user.notifications.filter(is_read=False).count()
    
    # Add context for team invitations (check if user is already a member)
    from teams.models import Team
    for notification in notifications:
        if notification.notification_type == 'team_invite' and notification.team_id:
            try:
                team = Team.objects.get(id=notification.team_id)
                notification.is_already_member = request.user in team.members.all()
                notification.team_name = team.name
            except Team.DoesNotExist:
                notification.is_already_member = False
                notification.team_exists = False
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count
    }
    return render(request, 'notifications/list.html', context)


@login_required
def mark_as_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('notifications:list')


@login_required
def mark_all_read(request):
    """Mark all notifications as read"""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('notifications:list')


@login_required
def accept_team_invite_notification(request, notification_id):
    """Accept team invitation from notification"""
    try:
        notification = get_object_or_404(Notification, 
                                       id=notification_id, 
                                       user=request.user,
                                       notification_type='team_invite')
    except Exception as e:
        messages.error(request, f'Notification not found or invalid. Error: {str(e)}')
        return redirect('notifications:list')
    
    # Get the team invite
    if notification.team_invite_id:
        try:
            # Find the team invite by team and user email
            team = Team.objects.get(id=notification.team_id)
            print(f"DEBUG: Looking for team invite - team_invite_id: {notification.team_invite_id}")
            print(f"DEBUG: User email: '{request.user.email}'")
            
            team_invite = TeamInvite.objects.get(
                id=notification.team_invite_id,
                team=team,
                email__iexact=request.user.email,  # Case-insensitive email comparison
                is_accepted=False
            )
            
            print(f"DEBUG: Found team invite: {team_invite.id}")
            print(f"DEBUG: Team invite email: '{team_invite.email}'")
            print(f"DEBUG: User is already member: {request.user in team.members.all()}")
            
            # Accept the invitation
            success, message = team_invite.accept_invite(request.user)
            
            print(f"DEBUG: Accept result - success: {success}, message: {message}")
            print(f"DEBUG: User is now member: {request.user in team.members.all()}")
            
            notification.mark_as_read()
            
            if success:
                messages.success(request, f'You have joined the team "{team.name}"!')
                return redirect('teams:detail', team_id=team.id)
            else:
                messages.error(request, message)
            
        except (Team.DoesNotExist, TeamInvite.DoesNotExist) as e:
            print(f"DEBUG: Team/TeamInvite not found: {str(e)}")
            
            # Check if user is already a member of the team
            if notification.team_id:
                try:
                    team = Team.objects.get(id=notification.team_id)
                    if request.user in team.members.all():
                        messages.info(request, f'You are already a member of the team "{team.name}".')
                        notification.mark_as_read()
                        return redirect('teams:detail', team_id=team.id)
                except Team.DoesNotExist:
                    pass
            
            messages.error(request, 'This invitation is no longer valid or has already been used.')
            notification.mark_as_read()
    else:
        messages.error(request, 'Invalid invitation - missing team invite ID.')
    
    return redirect('notifications:list')


@login_required
def get_unread_count(request):
    """Get unread notification count for AJAX"""
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'unread_count': count})


@login_required 
def get_recent_notifications(request):
    """Get recent unread notifications for dropdown preview"""
    notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')[:5]
    
    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': str(notification.id),
            'title': notification.title,
            'message': notification.message,
            'created_at': notification.created_at.strftime('%b %d, %H:%M'),
            'action_url': notification.action_url,
            'action_text': notification.action_text,
            'notification_type': notification.notification_type
        })
    
    return JsonResponse({
        'unread_count': len(notification_data),
        'notifications': notification_data
    })


@login_required
def debug_notifications(request):
    """Debug view to show all notifications for the user"""
    notifications = request.user.notifications.all().order_by('-created_at')
    
    debug_info = []
    for notification in notifications:
        debug_info.append({
            'id': str(notification.id),
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'is_read': notification.is_read,
            'created_at': notification.created_at,
            'action_url': notification.action_url,
            'team_invite_id': str(notification.team_invite_id) if notification.team_invite_id else None,
            'team_id': str(notification.team_id) if notification.team_id else None,
        })
    
    return JsonResponse({
        'user': request.user.email,
        'total_notifications': len(debug_info),
        'notifications': debug_info
    })


def create_team_invite_notification(user, team, invited_by, team_invite_id):
    """Helper function to create team invitation notification (prevents duplicates)"""
    # Check if a notification already exists for this user/team combination
    existing_notification = Notification.objects.filter(
        user=user,
        notification_type='team_invite',
        team_id=team.id,
        is_read=False
    ).first()
    
    if existing_notification:
        # Update the existing notification instead of creating a new one
        existing_notification.message = f'{invited_by.username} invited you to join the team "{team.name}".'
        existing_notification.team_invite_id = team_invite_id
        existing_notification.created_at = timezone.now()
        existing_notification.save()
        return existing_notification
    else:
        # Create new notification
        notification = Notification.objects.create(
            user=user,
            notification_type='team_invite',
            title=f'Team Invitation: {team.name}',
            message=f'{invited_by.username} invited you to join the team "{team.name}".',
            action_text='Accept Invitation',
            team_invite_id=team_invite_id,
            team_id=team.id
        )
        # Set the action_url after creation to use the notification's ID
        notification.action_url = f'/notifications/accept-invite/{notification.id}/'
        notification.save()
        
        return notification


@login_required
@require_http_methods(["POST"])
def update_preferences(request):
    """Update user notification preferences"""
    try:
        data = json.loads(request.body)
        
        prefs, created = NotificationPreferences.objects.get_or_create(
            user=request.user,
            defaults={
                'task_due_reminders': True,
                'weekly_summary': True,
                'team_updates': False
            }
        )
        
        # Update preferences
        if 'task_due_reminders' in data:
            prefs.task_due_reminders = data['task_due_reminders']
        if 'weekly_summary' in data:
            prefs.weekly_summary = data['weekly_summary']
        if 'team_updates' in data:
            prefs.team_updates = data['team_updates']
        
        prefs.save()
        
        return JsonResponse({'success': True, 'message': 'Preferences updated successfully'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def get_preferences(request):
    """Get user notification preferences"""
    prefs, created = NotificationPreferences.objects.get_or_create(
        user=request.user,
        defaults={
            'task_due_reminders': True,
            'weekly_summary': True,
            'team_updates': False
        }
    )
    
    return JsonResponse({
        'task_due_reminders': prefs.task_due_reminders,
        'weekly_summary': prefs.weekly_summary,
        'team_updates': prefs.team_updates,
    })
