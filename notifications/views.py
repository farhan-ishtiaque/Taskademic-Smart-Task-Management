from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Notification
from teams.models import TeamInvite, Team


@login_required
def notification_list(request):
    """Display user's notifications"""
    notifications = request.user.notifications.all()[:20]  # Latest 20
    unread_count = request.user.notifications.filter(is_read=False).count()
    
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
    
    if request.headers.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('notifications:list')


@login_required
def mark_all_read(request):
    """Mark all notifications as read"""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    if request.headers.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('notifications:list')


@login_required
def accept_team_invite_notification(request, notification_id):
    """Accept team invitation from notification"""
    notification = get_object_or_404(Notification, 
                                   id=notification_id, 
                                   user=request.user,
                                   notification_type='team_invite')
    
    # Get the team invite
    if notification.team_invite_id:
        try:
            # Find the team invite by team and user email
            team = Team.objects.get(id=notification.team_id)
            team_invite = TeamInvite.objects.get(
                id=notification.team_invite_id,
                team=team,
                email=request.user.email,
                is_accepted=False
            )
            
            # Accept the invitation
            team_invite.accept_invite(request.user)
            notification.mark_as_read()
            
            messages.success(request, f'You have joined the team "{team.name}"!')
            return redirect('teams:detail', team_id=team.id)
            
        except (Team.DoesNotExist, TeamInvite.DoesNotExist):
            messages.error(request, 'This invitation is no longer valid.')
            notification.mark_as_read()
    
    return redirect('notifications:list')


@login_required
def get_unread_count(request):
    """Get unread notification count for AJAX"""
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'unread_count': count})


def create_team_invite_notification(user, team, invited_by, team_invite_id):
    """Helper function to create team invitation notification"""
    Notification.objects.create(
        user=user,
        notification_type='team_invite',
        title=f'Team Invitation: {team.name}',
        message=f'{invited_by.username} invited you to join the team "{team.name}".',
        action_url=f'/notifications/accept-invite/{team_invite_id}/',
        action_text='Accept Invitation',
        team_invite_id=team_invite_id,
        team_id=team.id
    )
