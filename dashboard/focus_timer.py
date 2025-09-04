from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from tasks.models import Task
from django.utils import timezone
from datetime import timedelta
import json

@login_required
def focus_timer(request):
    """Focus Timer view using Pomodoro technique with smart task selection"""
    
    # Get today's tasks for focus session using priority scoring
    today = timezone.now().date()
    
    # Get all user tasks and sort by priority score in Python
    user_tasks = Task.objects.filter(
        user=request.user,
        status__in=['todo', 'in_progress']
    ).order_by('due_date')
    
    print(f"DEBUG: Found {user_tasks.count()} tasks for user {request.user.username}")
    for task in user_tasks:
        moscow_details = task.get_moscow_details()
        print(f"  - {task.title}: priority={task.priority}, status={task.status}, score={moscow_details['score']}")
    
    # Convert to list and sort by priority score (calculated in Python)
    user_tasks = list(user_tasks)
    user_tasks.sort(key=lambda x: x.get_moscow_details()['score'], reverse=True)
    
    # Separate tasks by calculated priority for 1-3-5 method
    # Big Things: Tasks with highest priority scores (urgent/overdue)
    big_tasks = [task for task in user_tasks if task.get_moscow_details()['score'] >= 400][:1]
    
    # Medium Things: High-medium priority tasks
    medium_tasks = [task for task in user_tasks if 200 <= task.get_moscow_details()['score'] < 400][:3]
    
    # Small Things: Lower priority or quick tasks
    small_tasks = [task for task in user_tasks if task.get_moscow_details()['score'] < 200][:5]
    
    # If not enough tasks in categories, fill from general pool
    if not big_tasks:
        big_tasks = user_tasks[:1]
    
    if len(medium_tasks) < 3:
        needed = 3 - len(medium_tasks)
        used_task_ids = [t.id for t in big_tasks] + [t.id for t in medium_tasks]
        extra_medium = [t for t in user_tasks if t.id not in used_task_ids][:needed]
        medium_tasks = medium_tasks + extra_medium
    
    if len(small_tasks) < 5:
        needed = 5 - len(small_tasks)
        used_task_ids = [t.id for t in big_tasks] + [t.id for t in medium_tasks] + [t.id for t in small_tasks]
        extra_small = [t for t in user_tasks if t.id not in used_task_ids][:needed]
        small_tasks = small_tasks + extra_small
    
    context = {
        'must_do_tasks': big_tasks,        # 1 Big Thing
        'should_do_tasks': medium_tasks[:3],  # 3 Medium Things  
        'could_do_tasks': small_tasks[:5],    # 5 Small Things
        'today': today,
        'all_tasks_count': len(user_tasks),
    }
    
    return render(request, 'dashboard/focus_timer.html', context)


@csrf_exempt
@login_required
def complete_task_ajax(request):
    """AJAX endpoint to mark task as completed"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id')
            
            task = Task.objects.get(id=task_id, user=request.user)
            task.status = 'done'
            task.completed_at = timezone.now()
            task.save()
            
            # Update user points (if you have a UserProfile model)
            try:
                profile = request.user.userprofile
                profile.total_points += 10  # 10 points per completed task
                profile.save()
            except:
                pass  # UserProfile might not exist
            
            return JsonResponse({
                'success': True,
                'message': 'Task completed successfully!',
                'task_id': task_id
            })
            
        except Task.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Task not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
@login_required
def update_timer_session(request):
    """AJAX endpoint to track timer sessions"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_type = data.get('session_type', 'pomodoro')
            duration = data.get('duration', 25)
            completed_tasks = data.get('completed_tasks', [])
            
            # Here you could save to a FocusSession model if you have one
            # For now, just return success
            
            return JsonResponse({
                'success': True,
                'message': f'{session_type.title()} session completed!',
                'duration': duration,
                'tasks_completed': len(completed_tasks)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
