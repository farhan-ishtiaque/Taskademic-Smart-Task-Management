from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import json
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Task, TimeBlock
from .serializers import TaskSerializer, TaskCreateSerializer, TimeBlockSerializer, KanbanBoardSerializer
from .forms import TaskForm

logger = logging.getLogger(__name__)


@login_required
def task_list(request):
    """Display all tasks for the current user"""
    tasks = Task.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'tasks/list.html', {'tasks': tasks})


@login_required
def task_create(request):
    """Create a new task with automatic priority calculation"""
    
    if request.method == 'POST':
        print(f"DEBUG: POST data: {request.POST}")
        form = TaskForm(request.POST, user=request.user)  # Pass user to form
        print(f"DEBUG: Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"DEBUG: Form errors: {form.errors}")
            print(f"DEBUG: Form non-field errors: {form.non_field_errors()}")

        
        if form.is_valid():
            try:
                # Create the task with form data
                task = form.save(commit=False)
                task.user = request.user
                
                # Save first to get the ID, then calculate priority
                task.save()
                
                # Calculate priority information using MoSCoW
                moscow_details = task.get_moscow_details()
                moscow_priority = task.get_moscow_priority()
                
                messages.success(request, 
                    f'Task "{task.title}" created successfully! '
                    f'MoSCoW: {moscow_priority.title()} Have | '
                    f'Score: {moscow_details["score"]} | '
                    f'Type: {moscow_details["task_type"]}'
                )
                
                # Return JSON for AJAX requests
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({
                        'success': True,
                        'message': 'Task created successfully!',
                        'task_id': task.id,
                        'priority_score': moscow_details["score"],
                        'auto_priority': moscow_priority
                    })
                
                return redirect('dashboard:home')
                
            except Exception as e:
                messages.error(request, f'Error creating task: {str(e)}')
                return render(request, 'tasks/create.html', {'form': form})
        else:
            # Form has validation errors
            return render(request, 'tasks/create.html', {'form': form})
    
    # GET request - display empty form

    print("DEBUG: GET request - showing empty form")
    form = TaskForm(user=request.user)  # Pass user to form

    return render(request, 'tasks/create.html', {'form': form})


@login_required
@require_http_methods(["POST"])
def task_complete(request, task_id):
    """Mark a task as complete"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if task.status != 'done':
        task.mark_complete()
        messages.success(request, f'Task "{task.title}" completed! +10 points')
    
    return redirect('dashboard:home')


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def task_toggle(request, task_id):
    """Toggle task completion status via AJAX"""
    try:
        task = get_object_or_404(Task, id=task_id)
        
        # Check if user has permission to modify this task
        if task.user != request.user and task.assigned_to != request.user:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        # Parse request body
        data = json.loads(request.body)
        completed = data.get('completed', False)
        
        if completed:
            # Mark as complete and delete from Google Calendar
            if task.status != 'done':
                task.mark_complete()
                
                # Try to delete from Google Calendar if it exists
                try:
                    from calendar_sync.services import GoogleCalendarService
                    calendar_service = GoogleCalendarService(request.user)
                    calendar_service.delete_event(task)
                except Exception as e:
                    # Calendar deletion failed, but task completion should still succeed
                    print(f"Failed to delete from Google Calendar: {e}")
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Task "{task.title}" completed! +10 points',
                    'remove_task': True  # Signal to remove from UI
                })
        else:
            # Mark as incomplete
            task.status = 'todo'
            task.completed_at = None
            task.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'Task "{task.title}" marked as incomplete',
                'remove_task': False
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def task_edit(request, task_id):
    """Edit an existing task"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)  # Pass user
        if form.is_valid():
            try:
                # Save the updated task
                updated_task = form.save(commit=False)
                updated_task.user = request.user
                updated_task.save()
                
                messages.success(request, f'Task "{updated_task.title}" updated successfully!')
                
                # Return JSON for AJAX requests
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({
                        'success': True,
                        'message': 'Task updated successfully!',
                        'task_id': updated_task.id
                    })
                
                return redirect('tasks:kanban_board')
                
            except Exception as e:
                messages.error(request, f'Error updating task: {str(e)}')
                return render(request, 'tasks/edit.html', {'form': form, 'task': task})
        else:
            return render(request, 'tasks/edit.html', {'form': form, 'task': task})
    
    # GET request - display form with current task data
    form = TaskForm(instance=task, user=request.user)  # Pass user
    return render(request, 'tasks/edit.html', {'form': form, 'task': task})


@login_required
def task_edit_select(request):
    """Display list of tasks to select for editing"""
    tasks = Task.objects.filter(user=request.user).exclude(status='done').order_by('-created_at')
    return render(request, 'tasks/edit_select.html', {'tasks': tasks})


@login_required
def task_delete_select(request):
    """Display list of tasks to select for deletion"""
    tasks = Task.objects.filter(user=request.user).exclude(status='done').order_by('-created_at')
    return render(request, 'tasks/delete_select.html', {'tasks': tasks})


@login_required
def task_delete(request, task_id):
    """Delete a specific task"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        task_title = task.title
        # Google Calendar deletion is handled automatically by signals
        task.delete()
        messages.success(request, f'Task "{task_title}" has been deleted successfully.')
        return redirect('dashboard:home')
    
    return render(request, 'tasks/delete_confirm.html', {'task': task})


@login_required
def kanban_board(request):
    """Personal Kanban board view"""
    return render(request, 'tasks/kanban_board.html')


@login_required
def team_kanban_board(request, team_id):
    """Team Kanban board view showing all team tasks"""
    from teams.models import Team
    
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is a team member
    if request.user not in team.members.all():
        messages.error(request, "You don't have access to this team's board.")
        return redirect('teams:list')
    
    context = {
        'team': team,
        'is_team_board': True,
    }
    return render(request, 'tasks/team_kanban_board.html', context)


@login_required
def task_calendar(request):
    """Calendar view for tasks"""
    # Handle AJAX request for tasks
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.http import JsonResponse
        try:
            # Get tasks for the current user
            tasks = []
            if request.user.is_authenticated:
                # Use raw SQL to avoid model field issues
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, title, description, due_date, priority, status 
                        FROM tasks_task 
                        WHERE user_id = %s AND due_date IS NOT NULL
                        ORDER BY due_date
                    """, [request.user.id])
                    for row in cursor.fetchall():
                        tasks.append({
                            'id': row[0],
                            'title': row[1],
                            'description': row[2] or '',
                            'due_date': row[3].isoformat() if row[3] else None,
                            'priority': row[4],
                            'status': row[5],
                            'category': 'work'  # Default category
                        })
            
            return JsonResponse(tasks, safe=False)
        except Exception as e:
            print(f"Calendar AJAX error: {e}")
            import traceback
            print(traceback.format_exc())
            return JsonResponse([], safe=False)
    
    # For non-AJAX requests, provide server-side data as context
    from django.utils import timezone
    today = timezone.now().date()
    
    # Get today's tasks for server-side rendering
    todays_tasks = Task.objects.filter(
        user=request.user,
        due_date__date=today
    ).order_by('priority', 'created_at')
    
    context = {
        'todays_tasks': todays_tasks,
        'today': today,
    }
    
    return render(request, 'tasks/calendar.html', context)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """
        Override get_object to ensure user has access to the task.
        """
        pk = self.kwargs.get('pk')
        if pk:
            try:
                # Get the task directly, ensuring user has access
                task = Task.objects.filter(
                    Q(user=self.request.user) | Q(team__members=self.request.user)
                ).get(pk=pk)
                return task
            except Task.DoesNotExist:
                from django.http import Http404
                raise Http404("Task not found or access denied")
        return super().get_object()
    
    def get_queryset(self):
        try:
            # Simple query without union to improve performance
            user = self.request.user
            queryset = Task.objects.filter(
                Q(user=user) | Q(team__members=user)
            ).distinct().order_by('-created_at')
            
            print(f"TaskViewSet: Found {queryset.count()} tasks for user {user}")
        except Exception as e:
            print(f"TaskViewSet error: {e}")
            queryset = Task.objects.none()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority (MoSCoW)
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Team filter
        team_id = self.request.query_params.get('team', None)
        if team_id:
            queryset = queryset.filter(team_id=team_id)
        elif team_id == 'personal':
            queryset = queryset.filter(team__isnull=True)
        
        # Search by title or description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset
    
    def update(self, request, *args, **kwargs):
        """Override update to handle Google Calendar deletion when task is completed"""
        task = self.get_object()
        old_status = task.status
        
        # Perform the update first for fast response
        response = super().update(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Check if task was moved to done - do this asynchronously
            new_status = request.data.get('status')
            if new_status == 'done' and old_status != 'done':
                # Use threading to handle Google Calendar deletion in background
                import threading
                def delete_from_calendar():
                    try:
                        from calendar_sync.services import GoogleCalendarService
                        calendar_service = GoogleCalendarService(request.user)
                        calendar_service.delete_event(task)
                        print(f"Task {task.id} removed from Google Calendar")
                    except Exception as e:
                        print(f"Failed to delete from Google Calendar: {e}")
                
                # Start background thread for calendar deletion
                threading.Thread(target=delete_from_calendar, daemon=True).start()
        
        return response
    
    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to handle Google Calendar deletion when task is completed"""
        task = self.get_object()
        old_status = task.status
        
        # Perform the update first for fast response
        response = super().partial_update(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Check if task was moved to done - do this asynchronously
            new_status = request.data.get('status')
            if new_status == 'done' and old_status != 'done':
                # Use threading to handle Google Calendar deletion in background
                import threading
                def delete_from_calendar():
                    try:
                        from calendar_sync.services import GoogleCalendarService
                        calendar_service = GoogleCalendarService(request.user)
                        calendar_service.delete_event(task)
                        print(f"Task {task.id} removed from Google Calendar")
                    except Exception as e:
                        print(f"Failed to delete from Google Calendar: {e}")
                
                # Start background thread for calendar deletion
                threading.Thread(target=delete_from_calendar, daemon=True).start()
        
        return response
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def complete_task(self, request, pk=None):
        """Mark task as completed and award points"""
        task = self.get_object()
        if task.status != 'done':
            task.mark_complete()
            return Response({
                'message': 'Task completed successfully!',
                'points_earned': 10,
                'task': TaskSerializer(task, context={'request': request}).data
            })
        return Response({'message': 'Task already completed'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def kanban_board_data(self, request):
        """Get tasks organized by Kanban board columns"""
        # Optimized query with minimal data needed for Kanban
        all_tasks = Task.objects.filter(
            Q(user=request.user) | Q(team__members=request.user),
            status__in=['todo', 'in_progress', 'review', 'done']
        ).distinct().select_related('user', 'assigned_to').only(
            'id', 'title', 'description', 'status', 'priority', 'due_date', 
            'user_id', 'assigned_to_id', 'created_at'
        )
        
        # Organize tasks by status using list comprehension for better performance
        data = {
            'todo': [TaskSerializer(task, context={'request': request}).data for task in all_tasks if task.status == 'todo'],
            'in_progress': [TaskSerializer(task, context={'request': request}).data for task in all_tasks if task.status == 'in_progress'],
            'review': [TaskSerializer(task, context={'request': request}).data for task in all_tasks if task.status == 'review'],
            'done': [TaskSerializer(task, context={'request': request}).data for task in all_tasks if task.status == 'done']
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def team_kanban_data(self, request):
        """Get tasks organized by Kanban board columns for a specific team"""
        team_id = request.query_params.get('team_id')
        if not team_id:
            return Response({'error': 'team_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get team tasks where user has access
        from teams.models import Team
        try:
            team = Team.objects.get(id=team_id)
            if request.user not in team.members.all():
                return Response({'error': 'No access to this team'}, status=status.HTTP_403_FORBIDDEN)
        except Team.DoesNotExist:
            return Response({'error': 'Team not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get all team tasks regardless of assignment
        tasks = Task.objects.filter(team=team, status__in=['todo', 'in_progress', 'review', 'done'])
        
        # Organize tasks by status
        todo_tasks = tasks.filter(status='todo')
        in_progress_tasks = tasks.filter(status='in_progress')
        review_tasks = tasks.filter(status='review')
        done_tasks = tasks.filter(status='done')
        
        data = {
            'todo': TaskSerializer(todo_tasks, many=True, context={'request': request}).data,
            'in_progress': TaskSerializer(in_progress_tasks, many=True, context={'request': request}).data,
            'review': TaskSerializer(review_tasks, many=True, context={'request': request}).data,
            'done': TaskSerializer(done_tasks, many=True, context={'request': request}).data,
            'team': {
                'id': str(team.id),
                'name': team.name,
                'member_count': team.member_count,
                'members': [{'id': m.id, 'username': m.username, 'full_name': m.get_full_name()} for m in team.members.all()]
            }
        }
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def assign_to_member(self, request, pk=None):
        """Assign task to a team member"""
        task = self.get_object()
        
        # Check if user can assign this task
        if not task.can_be_edited_by(request.user):
            return Response({'error': 'No permission to edit this task'}, status=status.HTTP_403_FORBIDDEN)
        
        member_id = request.data.get('member_id')
        if not member_id:
            # Unassign task
            task.assigned_to = None
            task.save()
            return Response({'message': 'Task unassigned successfully'})
        
        try:
            from django.contrib.auth.models import User
            member = User.objects.get(id=member_id)
            
            # Check if member is in the task's team
            if task.team and member not in task.team.members.all():
                return Response({'error': 'User is not a member of this team'}, status=status.HTTP_400_BAD_REQUEST)
            
            task.assigned_to = member
            task.save()
            
            return Response({
                'message': f'Task assigned to {member.get_full_name() or member.username}',
                'task': TaskSerializer(task, context={'request': request}).data
            })
            
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change task status (for team collaboration)"""
        task = self.get_object()
        
        # Check if user can change status
        if not task.can_change_status(request.user):
            return Response({'error': 'No permission to change status'}, status=status.HTTP_403_FORBIDDEN)
        
        new_status = request.data.get('status')
        if new_status not in ['todo', 'in_progress', 'review', 'done']:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        task.status = new_status
        if new_status == 'done' and not task.completed_at:
            task.completed_at = timezone.now()
        task.save()
        
        return Response({
            'message': f'Task status changed to {new_status}',
            'task': TaskSerializer(task, context={'request': request}).data
        })
    
    @action(detail=False, methods=['get'])
    def moscow_prioritized(self, request):
        """Get tasks organized by MoSCoW priority"""
        tasks = self.get_queryset().filter(status__in=['todo', 'in_progress'])
        
        data = {
            'must': tasks.filter(priority='must'),
            'should': tasks.filter(priority='should'),
            'could': tasks.filter(priority='could'),
            'wont': tasks.filter(priority='wont')
        }
        
        serialized_data = {}
        for priority_key, task_queryset in data.items():
            serialized_data[priority_key] = TaskSerializer(
                task_queryset, many=True, context={'request': request}
            ).data
        
        return Response(serialized_data)
    
    @action(detail=False, methods=['get'])
    def overdue_tasks(self, request):
        """Get overdue tasks"""
        now = timezone.now()
        overdue_tasks = self.get_queryset().filter(
            due_date__lt=now,
            status__in=['todo', 'in_progress']
        )
        
        serializer = TaskSerializer(overdue_tasks, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today_tasks(self, request):
        """Get tasks due today"""
        today = timezone.now().date()
        today_tasks = self.get_queryset().filter(
            due_date__date=today
        )
        
        serializer = TaskSerializer(today_tasks, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def team_kanban_data(self, request):
        """Get team Kanban board data"""
        team_id = request.query_params.get('team_id')
        
        if not team_id:
            return Response({'error': 'team_id required'}, status=400)
        
        try:
            from teams.models import Team
            team = Team.objects.get(id=team_id)
            
            # Simple check - user must be team member
            if request.user not in team.members.all():
                return Response({'error': 'Access denied'}, status=403)
            
        except Team.DoesNotExist:
            return Response({'error': 'Team not found'}, status=404)
        
        tasks = Task.objects.filter(team=team)
        
        data = {
            'todo': TaskSerializer(tasks.filter(status='todo'), many=True, context={'request': request}).data,
            'in_progress': TaskSerializer(tasks.filter(status='in_progress'), many=True, context={'request': request}).data,
            'review': TaskSerializer(tasks.filter(status='review'), many=True, context={'request': request}).data,
            'done': TaskSerializer(tasks.filter(status='done'), many=True, context={'request': request}).data,
        }
        
        return Response(data)


class TimeBlockViewSet(viewsets.ModelViewSet):
    serializer_class = TimeBlockSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TimeBlock.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_statistics(request):
    """Get task statistics for the user"""
    user = request.user
    tasks = Task.objects.filter(user=user)
    
    # Basic stats
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='done').count()
    pending_tasks = tasks.filter(status__in=['todo', 'in_progress']).count()
    overdue_tasks = tasks.filter(
        due_date__lt=timezone.now(),
        status__in=['todo', 'in_progress']
    ).count()
    
    # Category breakdown
    category_stats = {}
    for category_choice in Task.CATEGORY_CHOICES:
        category_key = category_choice[0]
        category_stats[category_key] = {
            'total': tasks.filter(category=category_key).count(),
            'completed': tasks.filter(category=category_key, status='done').count()
        }
    
    # Priority breakdown (MoSCoW)
    priority_stats = {}
    for priority_choice in Task.PRIORITY_CHOICES:
        priority_key = priority_choice[0]
        priority_stats[priority_key] = {
            'total': tasks.filter(priority=priority_key).count(),
            'completed': tasks.filter(priority=priority_key, status='done').count()
        }
    
    return Response({
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        'category_breakdown': category_stats,
        'priority_breakdown': priority_stats
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def smart_schedule_suggestion(request):
    """Suggest optimal schedule based on user's preferred technique"""
    user = request.user
    profile = user.userprofile
    pending_tasks = Task.objects.filter(
        user=user,
        status__in=['todo', 'in_progress']
    ).order_by('due_date', 'priority')
    
    suggestions = []
    technique = profile.preferred_technique
    
    if technique == 'pomodoro':
        # 25-minute work blocks with 5-minute breaks
        for task in pending_tasks[:8]:  # Limit to 8 tasks for example
            work_blocks = max(1, task.estimated_duration // 25)
            suggestions.append({
                'task': TaskSerializer(task).data,
                'technique': 'Pomodoro',
                'work_blocks': work_blocks,
                'total_time': work_blocks * 30,  # 25 min work + 5 min break
                'suggestion': f"Break this into {work_blocks} Pomodoro sessions"
            })
    
    elif technique == '52_17':
        # 52-minute work blocks with 17-minute breaks
        for task in pending_tasks[:6]:  # Limit to 6 tasks
            work_blocks = max(1, task.estimated_duration // 52)
            suggestions.append({
                'task': TaskSerializer(task).data,
                'technique': '52/17 Rule',
                'work_blocks': work_blocks,
                'total_time': work_blocks * 69,  # 52 min work + 17 min break
                'suggestion': f"Allocate {work_blocks} focused session(s) of 52 minutes each"
            })
    
    elif technique == '1_3_5':
        # 1 big, 3 medium, 5 small tasks
        must_tasks = pending_tasks.filter(priority='must')[:1]
        should_tasks = pending_tasks.filter(priority='should')[:3]
        could_tasks = pending_tasks.filter(priority='could')[:5]
        
        suggestions.append({
            'technique': '1-3-5 Rule',
            'big_task': TaskSerializer(must_tasks, many=True).data,
            'medium_tasks': TaskSerializer(should_tasks, many=True).data,
            'small_tasks': TaskSerializer(could_tasks, many=True).data,
            'suggestion': "Focus on 1 big task, 3 medium tasks, and 5 small tasks today"
        })
    
    return Response({
        'preferred_technique': technique,
        'suggestions': suggestions
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_team_members(request, team_id):
    """Get members of a specific team for assignment dropdown"""
    from teams.models import Team
    
    try:
        team = Team.objects.get(id=team_id)
        if request.user not in team.members.all():
            return Response({'error': 'No access to this team'}, status=status.HTTP_403_FORBIDDEN)
        
        members = team.members.all()
        member_data = [
            {
                'id': member.id,
                'username': member.username,
                'full_name': member.get_full_name() or member.username,
                'email': member.email
            }
            for member in members
        ]
        
        return Response(member_data)
        
    except Team.DoesNotExist:
        return Response({'error': 'Team not found'}, status=status.HTTP_404_NOT_FOUND)
