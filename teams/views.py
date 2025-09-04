from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Team, TeamInvite
from .forms import TeamCreateForm, EmailInviteForm


# Simple status/debug view
@login_required
def team_status(request):
    """Debug view to check team system status"""
    from django.db.models import Count
    
    context = {
        'total_teams': Team.objects.count(),
        'total_invites': TeamInvite.objects.count(),
        'pending_invites': TeamInvite.objects.filter(is_accepted=False, expires_at__gt=timezone.now()).count(),
        'accepted_invites': TeamInvite.objects.filter(is_accepted=True).count(),
        'recent_teams': Team.objects.order_by('-created_at')[:5],
        'recent_invites': TeamInvite.objects.order_by('-created_at')[:10],
    }
    return render(request, 'teams/status.html', context)


@login_required
def team_list(request):
    """Display user's teams"""
    user_teams = request.user.teams.all()
    return render(request, 'teams/list.html', {'teams': user_teams})


@login_required
def team_create(request):
    """Create a new team"""
    if request.method == 'POST':
        form = TeamCreateForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.created_by = request.user
            team.save()
            messages.success(request, f'Team "{team.name}" created successfully!')
            return redirect('teams:detail', team_id=team.id)
    else:
        form = TeamCreateForm()
    
    return render(request, 'teams/create.html', {'form': form})


@login_required
def team_detail(request, team_id):
    """Team Kanban board with invite management"""
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is a member
    if request.user not in team.members.all():
        messages.error(request, "You're not a member of this team.")
        return redirect('teams:list')
    
    # Get pending invites
    pending_invites = team.email_invites.filter(is_accepted=False, expires_at__gt=timezone.now())
    
    return render(request, 'teams/detail.html', {
        'team': team,
        'members': team.members.all(),
        'invite_code': team.invite_code,
        'pending_invites': pending_invites,
        'email_invite_form': EmailInviteForm()
    })


@login_required
def team_join(request):
    """Join team using invite code"""
    if request.method == 'POST':
        invite_code = request.POST.get('invite_code', '').upper()
        
        try:
            team = Team.objects.get(invite_code=invite_code)
            
            if request.user in team.members.all():
                messages.info(request, "You're already a member of this team.")
            else:
                team.members.add(request.user)
                messages.success(request, f'Successfully joined team "{team.name}"!')
            
            return redirect('teams:detail', team_id=team.id)
            
        except Team.DoesNotExist:
            messages.error(request, 'Invalid invite code.')
    
    return render(request, 'teams/join.html')


@login_required
def team_invite_email(request, team_id):
    """Send email invitation to join team"""
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is a team member
    if request.user not in team.members.all():
        messages.error(request, "You're not a member of this team.")
        return redirect('teams:list')
    
    if request.method == 'POST':
        form = EmailInviteForm(request.POST)
        print(f"DEBUG: Form data: {request.POST}")
        print(f"DEBUG: Email from POST: '{request.POST.get('email', 'NOT_FOUND')}'")
        print(f"DEBUG: CSRF token present: {bool(request.POST.get('csrfmiddlewaretoken'))}")
        print(f"DEBUG: Form is valid: {form.is_valid()}")
        
        if form.is_valid():
            email = form.cleaned_data['email']
            print(f"DEBUG: Inviting email: {email}")
            
            try:
                # Validate email format
                validate_email(email)
                
                # Check if user already exists and is a member
                try:
                    existing_user = User.objects.filter(email=email).first()
                    if existing_user and existing_user in team.members.all():
                        print(f"DEBUG: User {email} is already a member")
                        messages.warning(request, f"{email} is already a member of this team.")
                        return redirect('teams:detail', team_id=team.id)
                except User.DoesNotExist:
                    pass
                
                # Check if there's already a pending invite
                existing_invite = TeamInvite.objects.filter(
                    team=team,
                    email=email,
                    is_accepted=False,
                    expires_at__gt=timezone.now()
                ).first()
                
                if existing_invite:
                    print(f"DEBUG: Existing invite found for {email}")
                    messages.info(request, f"An invitation has already been sent to {email}.")
                    return redirect('teams:detail', team_id=team.id)
                
                # Create new invitation
                print(f"DEBUG: Creating new invite for {email}")
                invite = TeamInvite.objects.create(
                    team=team,
                    email=email,
                    invited_by=request.user
                )
                print(f"DEBUG: Created invite with ID: {invite.id}")
                
                # Check if user is registered on the website
                try:
                    registered_user = User.objects.filter(email=email).first()
                    if registered_user:
                        print(f"DEBUG: User {email} is registered, sending notification")
                        # User is registered - send in-app notification
                        from notifications.views import create_team_invite_notification
                        create_team_invite_notification(registered_user, team, request.user, invite.id)
                        print(f"DEBUG: Notification created successfully")
                        messages.success(request, f"In-app notification sent to {email} (registered user)!")
                    else:
                        print(f"DEBUG: User {email} is not registered, sending email")
                        # User not registered - send email invitation
                        if invite.send_invite_email():
                            print(f"DEBUG: Email sent successfully")
                            messages.success(request, f"Email invitation sent to {email} (unregistered user)!")
                        else:
                            print(f"DEBUG: Email sending failed")
                            messages.error(request, f"Failed to send invitation to {email}. Please try again.")
                    
                except Exception as e:
                    print(f"DEBUG: Exception occurred: {e}")
                    # Fallback to email invitation if there's any issue
                    if invite.send_invite_email():
                        messages.success(request, f"Email invitation sent to {email}!")
                    else:
                        messages.error(request, f"Failed to send invitation to {email}. Please try again.")
                
            except ValidationError as e:
                print(f"DEBUG: Validation error: {e}")
                messages.error(request, "Please enter a valid email address.")
        else:
            print(f"DEBUG: Form errors: {form.errors}")
            messages.error(request, "Please correct the form errors.")
    
    return redirect('teams:detail', team_id=team.id)


def accept_invite(request, invite_token):
    """Accept email invitation (public view)"""
    invite = get_object_or_404(TeamInvite, invite_token=invite_token)
    
    if not invite.is_valid:
        if invite.is_expired:
            messages.error(request, "This invitation has expired.")
        else:
            messages.error(request, "This invitation has already been accepted.")
        return redirect('accounts:login')
    
    if request.user.is_authenticated:
        # User is logged in - try to accept invite
        success, message = invite.accept_invite(request.user)
        if success:
            messages.success(request, message)
            return redirect('teams:detail', team_id=invite.team.id)
        else:
            messages.error(request, message)
            return redirect('teams:list')
    else:
        # User not logged in - store invite token in session and redirect to login
        request.session['pending_invite_token'] = invite_token
        messages.info(request, f"Please log in or create an account to join {invite.team.name}.")
        return redirect('accounts:login')


@login_required
def team_invite_username(request, team_id):
    """Invite member by username (existing functionality)"""
    team = get_object_or_404(Team, id=team_id)
    
    # Simple check - only team members can invite
    if request.user not in team.members.all():
        messages.error(request, "You're not a member of this team.")
        return redirect('teams:list')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        
        try:
            user_to_invite = User.objects.get(username=username)
            
            if user_to_invite in team.members.all():
                messages.warning(request, f"{username} is already a member.")
            else:
                team.members.add(user_to_invite)
                messages.success(request, f"Successfully added {username} to the team!")
                
        except User.DoesNotExist:
            messages.error(request, f"User '{username}' not found.")
    
    return redirect('teams:detail', team_id=team.id)


@login_required
def cancel_invite(request, team_id, invite_id):
    """Cancel pending email invitation"""
    team = get_object_or_404(Team, id=team_id)
    invite = get_object_or_404(TeamInvite, id=invite_id, team=team)
    
    # Check permissions
    if request.user not in team.members.all():
        messages.error(request, "You're not a member of this team.")
        return redirect('teams:list')
    
    if request.method == 'POST':
        invite.delete()
        messages.success(request, f"Invitation to {invite.email} has been cancelled.")
    
    return redirect('teams:detail', team_id=team.id)


class TeamViewSet(viewsets.ModelViewSet):
    """Simple Team API"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return self.request.user.teams.all()
    
    @action(detail=True, methods=['get'])
    def kanban_data(self, request, pk=None):
        """Get team Kanban board data"""
        team = self.get_object()
        
        if request.user not in team.members.all():
            return Response({'error': 'Access denied'}, status=403)
        
        from tasks.models import Task
        from tasks.serializers import TaskSerializer
        
        tasks = Task.objects.filter(team=team)
        
        data = {
            'todo': TaskSerializer(tasks.filter(status='todo'), many=True, context={'request': request}).data,
            'in_progress': TaskSerializer(tasks.filter(status='in_progress'), many=True, context={'request': request}).data,
            'review': TaskSerializer(tasks.filter(status='review'), many=True, context={'request': request}).data,
            'done': TaskSerializer(tasks.filter(status='done'), many=True, context={'request': request}).data,
        }
        
        return Response(data)


@login_required
def team_members_json(request, team_id):
    """Get team members as JSON for AJAX calls"""
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is a team member
    if request.user not in team.members.all():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    members = [
        {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
        for user in team.members.all()
    ]
    
    return JsonResponse({'members': members})


@login_required
def check_invite_status(request, team_id):
    """Check status of invitations and task assignments for a team"""
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is a team member
    if request.user not in team.members.all():
        messages.error(request, "You're not a member of this team.")
        return redirect('teams:list')
    
    # Get invite information
    pending_invites = team.email_invites.filter(is_accepted=False, expires_at__gt=timezone.now())
    accepted_invites = team.email_invites.filter(is_accepted=True)
    expired_invites = team.email_invites.filter(is_accepted=False, expires_at__lte=timezone.now())
    
    # Get task assignment information
    from tasks.models import Task
    team_tasks = Task.objects.filter(team=team)
    assigned_tasks = team_tasks.exclude(assigned_to__isnull=True)
    unassigned_tasks = team_tasks.filter(assigned_to__isnull=True)
    
    # Group tasks by assignee
    tasks_by_member = {}
    for member in team.members.all():
        member_tasks = team_tasks.filter(assigned_to=member)
        tasks_by_member[member.username] = {
            'total': member_tasks.count(),
            'todo': member_tasks.filter(status='todo').count(),
            'in_progress': member_tasks.filter(status='in_progress').count(),
            'review': member_tasks.filter(status='review').count(),
            'done': member_tasks.filter(status='done').count(),
        }
    
    context = {
        'team': team,
        'pending_invites': pending_invites,
        'accepted_invites': accepted_invites,
        'expired_invites': expired_invites,
        'team_tasks': team_tasks,
        'assigned_tasks': assigned_tasks,
        'unassigned_tasks': unassigned_tasks,
        'tasks_by_member': tasks_by_member,
        'total_members': team.members.count(),
    }
    
    return render(request, 'teams/invite_status.html', context)


@login_required
def search_users_api(request):
    """API endpoint to search users by email for team invites"""
    from django.http import JsonResponse
    from django.contrib.auth.models import User
    from django.db.models import Q
    
    query = request.GET.get('q', '').strip()
    team_id = request.GET.get('team_id', '')
    
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    # Get team to exclude existing members
    team = None
    if team_id:
        try:
            team = Team.objects.get(id=team_id)
            # Check if user has access to this team
            if request.user not in team.members.all():
                return JsonResponse({'error': 'Access denied'}, status=403)
        except Team.DoesNotExist:
            return JsonResponse({'error': 'Team not found'}, status=404)
    
    # Search users by email, username, or name
    users_query = User.objects.filter(
        Q(email__icontains=query) |
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).exclude(id=request.user.id).order_by('email')  # Exclude current user
    
    # Exclude team members if team is specified
    if team:
        users_query = users_query.exclude(id__in=team.members.values_list('id', flat=True))
    
    # Limit results
    users = users_query[:10]
    
    # Format response (remove duplicates by email)
    user_data = []
    seen_emails = set()
    
    for user in users:
        # Skip if we've already seen this email
        if user.email.lower() in seen_emails:
            continue
        seen_emails.add(user.email.lower())
        
        full_name = user.get_full_name().strip()
        display_name = full_name if full_name else user.username
        
        user_data.append({
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'display_name': display_name,
            'full_name': full_name,
            'initials': ''.join([name[0].upper() for name in display_name.split()[:2]])
        })
    
    return JsonResponse({'users': user_data})
