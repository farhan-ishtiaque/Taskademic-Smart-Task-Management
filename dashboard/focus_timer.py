from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from tasks.models import Task
from django.utils import timezone
from datetime import timedelta
from .models import ScheduledTask, DailySchedule
from priority_analyzer.signals import MoSCoWCacheService
import json

@login_required
def focus_timer(request):
    """Focus Timer view using Pomodoro technique with smart task selection"""
    
    # Get today's date
    today = timezone.now().date()
    
    # Check access source and selected task parameters
    selected_task_id = request.GET.get('task_id')
    selected_duration = request.GET.get('duration')
    source = request.GET.get('source')  # 'custom', 'ai', or None (direct access)
    selected_task = None
    
    if selected_task_id:
        try:
            selected_task = Task.objects.get(id=selected_task_id, user=request.user)
        except Task.DoesNotExist:
            selected_task = None

    # Get the daily schedule to check if there's a generated schedule for today
    daily_schedule = None
    try:
        daily_schedule = DailySchedule.objects.get(user=request.user, date=today)
    except DailySchedule.DoesNotExist:
        pass

    # Determine what tasks to show based on source
    if source == 'custom':
        # Show ONLY custom schedule tasks
        try:
            scheduled_tasks = ScheduledTask.objects.filter(
                user=request.user,
                scheduled_date=today,
                schedule_type='custom',  # Only custom schedule tasks
                task__status__in=['todo', 'in_progress', 'review']
            ).order_by('start_time')
        except Exception as e:
            print(f"ERROR: Could not filter custom tasks: {e}")
            # Fallback: show all scheduled tasks for today
            scheduled_tasks = ScheduledTask.objects.filter(
                user=request.user,
                scheduled_date=today,
                task__status__in=['todo', 'in_progress', 'review']
            ).order_by('start_time')
        
        print(f"DEBUG: Custom schedule mode - Found {scheduled_tasks.count()} custom scheduled tasks for {today}")
        
        # Apply MoSCoW analysis to scheduled tasks
        if scheduled_tasks.exists():
            result = MoSCoWCacheService.get_moscow_analysis(request.user)
            
            # Create task details mapping
            task_details = {}
            for log_entry in result['decision_log']:
                task_id = int(log_entry['id'])
                task_details[task_id] = {
                    'category': log_entry['final'],
                    'score': log_entry['score'],
                    'task_type': log_entry['type'],
                    'importance': log_entry['importance'],
                    'urgency': log_entry['urgency'],
                    'due_in_days': log_entry['due_in_days'],
                    'reasoning': log_entry['matched_rule']
                }
            
            # Apply MoSCoW analysis to scheduled tasks
            scheduled_tasks_list = list(scheduled_tasks)
            for scheduled_task in scheduled_tasks_list:
                if scheduled_task.task:
                    details = task_details.get(scheduled_task.task.id, {})
                    scheduled_task.task.moscow_category = details.get('category', 'should')
                    scheduled_task.task.moscow_score = details.get('score', 30)
                    scheduled_task.task.moscow_task_type = details.get('task_type', 'Regular coursework')
                    scheduled_task.task.moscow_reasoning = details.get('reasoning', 'Default classification')
                    scheduled_task.task.moscow_due_in_days = details.get('due_in_days')
            
            # Return context for custom schedule
            context = {
                'must_do_tasks': [st for st in scheduled_tasks_list if st.task and getattr(st.task, 'moscow_category', 'should') == 'must'],
                'should_do_tasks': [st for st in scheduled_tasks_list if st.task and getattr(st.task, 'moscow_category', 'should') == 'should'],
                'could_do_tasks': [st for st in scheduled_tasks_list if st.task and getattr(st.task, 'moscow_category', 'should') == 'could'],
                'wont_do_tasks': [st for st in scheduled_tasks_list if st.task and getattr(st.task, 'moscow_category', 'should') == 'wont'],
                'scheduled_tasks': scheduled_tasks_list,
                'daily_schedule': daily_schedule,
                'has_schedule': True,
                'source': 'custom',
                'today': today,
                'all_tasks_count': len(scheduled_tasks_list),
                'selected_task': selected_task,
                'selected_duration': selected_duration,
            }
        else:
            # No tasks in custom schedule, show empty state
            context = {
                'must_do_tasks': [],
                'should_do_tasks': [],
                'could_do_tasks': [],
                'wont_do_tasks': [],
                'scheduled_tasks': [],
                'daily_schedule': daily_schedule,
                'has_schedule': True,
                'source': 'custom',
                'today': today,
                'all_tasks_count': 0,
                'selected_task': selected_task,
                'selected_duration': selected_duration,
            }
            
    elif source == 'ai':
        # Show ONLY AI generated schedule tasks
        try:
            scheduled_tasks = ScheduledTask.objects.filter(
                user=request.user,
                scheduled_date=today,
                schedule_type='ai',  # Only AI generated tasks
                task__status__in=['todo', 'in_progress', 'review']
            ).order_by('start_time')
        except Exception as e:
            print(f"ERROR: Could not filter AI tasks: {e}")
            # Fallback: show all scheduled tasks for today
            scheduled_tasks = ScheduledTask.objects.filter(
                user=request.user,
                scheduled_date=today,
                task__status__in=['todo', 'in_progress', 'review']
            ).order_by('start_time')
        
        print(f"DEBUG: AI schedule mode - Found {scheduled_tasks.count()} AI scheduled tasks for {today}")
        
        # Apply MoSCoW analysis to scheduled tasks
        if scheduled_tasks.exists():
            result = MoSCoWCacheService.get_moscow_analysis(request.user)
            
            # Create task details mapping
            task_details = {}
            for log_entry in result['decision_log']:
                task_id = int(log_entry['id'])
                task_details[task_id] = {
                    'category': log_entry['final'],
                    'score': log_entry['score'],
                    'task_type': log_entry['type'],
                    'importance': log_entry['importance'],
                    'urgency': log_entry['urgency'],
                    'due_in_days': log_entry['due_in_days'],
                    'reasoning': log_entry['matched_rule']
                }
            
            # Apply MoSCoW analysis to scheduled tasks
            scheduled_tasks_list = list(scheduled_tasks)
            for scheduled_task in scheduled_tasks_list:
                if scheduled_task.task:
                    details = task_details.get(scheduled_task.task.id, {})
                    scheduled_task.task.moscow_category = details.get('category', 'should')
                    scheduled_task.task.moscow_score = details.get('score', 30)
                    scheduled_task.task.moscow_task_type = details.get('task_type', 'Regular coursework')
                    scheduled_task.task.moscow_reasoning = details.get('reasoning', 'Default classification')
                    scheduled_task.task.moscow_due_in_days = details.get('due_in_days')
            
            # Return context for AI schedule
            context = {
                'must_do_tasks': [st for st in scheduled_tasks_list if st.task and getattr(st.task, 'moscow_category', 'should') == 'must'],
                'should_do_tasks': [st for st in scheduled_tasks_list if st.task and getattr(st.task, 'moscow_category', 'should') == 'should'],
                'could_do_tasks': [st for st in scheduled_tasks_list if st.task and getattr(st.task, 'moscow_category', 'should') == 'could'],
                'wont_do_tasks': [st for st in scheduled_tasks_list if st.task and getattr(st.task, 'moscow_category', 'should') == 'wont'],
                'scheduled_tasks': scheduled_tasks_list,
                'daily_schedule': daily_schedule,
                'has_schedule': True,
                'source': 'ai',
                'today': today,
                'all_tasks_count': len(scheduled_tasks_list),
                'selected_task': selected_task,
                'selected_duration': selected_duration,
            }
        else:
            # No tasks in AI schedule, show empty state
            context = {
                'must_do_tasks': [],
                'should_do_tasks': [],
                'could_do_tasks': [],
                'wont_do_tasks': [],
                'scheduled_tasks': [],
                'daily_schedule': daily_schedule,
                'has_schedule': True,
                'source': 'ai',
                'today': today,
                'all_tasks_count': 0,
                'selected_task': selected_task,
                'selected_duration': selected_duration,
            }
            
    else:
        # Direct access (tab click) - Check if there's a schedule for today first
        # If there's a schedule, show those tasks. If not, show all tasks from MoSCoW matrix
        
        if daily_schedule:
            # There's a schedule for today - show scheduled tasks by priority
            try:
                all_scheduled_tasks = ScheduledTask.objects.filter(
                    user=request.user,
                    scheduled_date=today,
                    task__status__in=['todo', 'in_progress', 'review']
                ).order_by('start_time')
                
                # Determine the primary schedule type for display
                detected_source = 'ai'  # default
                if all_scheduled_tasks.exists():
                    schedule_types = set(all_scheduled_tasks.values_list('schedule_type', flat=True))
                    if 'ai' in schedule_types:
                        detected_source = 'ai'
                        scheduled_tasks = all_scheduled_tasks.filter(schedule_type='ai')
                    elif 'custom' in schedule_types:
                        detected_source = 'custom'
                        scheduled_tasks = all_scheduled_tasks.filter(schedule_type='custom')
                    else:
                        detected_source = 'mixed'
                        scheduled_tasks = all_scheduled_tasks
                else:
                    scheduled_tasks = ScheduledTask.objects.none()
                
                print(f"DEBUG: Direct access with schedule - detected source: {detected_source}, showing {scheduled_tasks.count()} scheduled tasks")
                
                # Apply MoSCoW analysis to scheduled tasks
                if scheduled_tasks.exists():
                    result = MoSCoWCacheService.get_moscow_analysis(request.user)
                    
                    # Create task details mapping
                    task_details = {}
                    for log_entry in result['decision_log']:
                        task_id = int(log_entry['id'])
                        task_details[task_id] = {
                            'category': log_entry['final'],
                            'score': log_entry['score'],
                            'task_type': log_entry['type'],
                            'importance': log_entry['importance'],
                            'urgency': log_entry['urgency'],
                            'due_in_days': log_entry['due_in_days'],
                            'reasoning': log_entry['matched_rule']
                        }
                    
                    # Apply MoSCoW analysis to scheduled tasks
                    scheduled_tasks_list = list(scheduled_tasks)
                    for scheduled_task in scheduled_tasks_list:
                        if scheduled_task.task:
                            details = task_details.get(scheduled_task.task.id, {})
                            scheduled_task.task.moscow_category = details.get('category', 'should')
                            scheduled_task.task.moscow_score = details.get('score', 30)
                            scheduled_task.task.moscow_task_type = details.get('task_type', 'Regular coursework')
                            scheduled_task.task.moscow_reasoning = details.get('reasoning', 'Default classification')
                            scheduled_task.task.moscow_due_in_days = details.get('due_in_days')
                    
                    # Return context for scheduled tasks
                    context = {
                        'must_do_tasks': [st for st in scheduled_tasks_list if st.task and getattr(st.task, 'moscow_category', 'should') == 'must'],
                        'should_do_tasks': [st for st in scheduled_tasks_list if st.task and getattr(st.task, 'moscow_category', 'should') == 'should'],
                        'could_do_tasks': [st for st in scheduled_tasks_list if st.task and getattr(st.task, 'moscow_category', 'should') == 'could'],
                        'wont_do_tasks': [st for st in scheduled_tasks_list if st.task and getattr(st.task, 'moscow_category', 'should') == 'wont'],
                        'scheduled_tasks': scheduled_tasks_list,
                        'daily_schedule': daily_schedule,
                        'has_schedule': True,
                        'source': detected_source,
                        'today': today,
                        'all_tasks_count': len(scheduled_tasks_list),
                        'selected_task': selected_task,
                        'selected_duration': selected_duration,
                    }
                else:
                    # Schedule exists but no tasks - show empty state
                    context = {
                        'must_do_tasks': [],
                        'should_do_tasks': [],
                        'could_do_tasks': [],
                        'wont_do_tasks': [],
                        'scheduled_tasks': [],
                        'daily_schedule': daily_schedule,
                        'has_schedule': True,
                        'source': detected_source,
                        'today': today,
                        'all_tasks_count': 0,
                        'selected_task': selected_task,
                        'selected_duration': selected_duration,
                    }
                    
            except Exception as e:
                print(f"ERROR: Could not load scheduled tasks: {e}")
                # Fallback to all tasks
                daily_schedule = None
        
        # No schedule exists - show all tasks from MoSCoW matrix (original behavior)
        if not daily_schedule:
            user_tasks = Task.objects.filter(
                user=request.user,
                status__in=['todo', 'in_progress']
            ).order_by('due_date')
            
            print(f"DEBUG: Direct access with NO schedule - showing all MoSCoW tasks. Found {user_tasks.count()} tasks for user {request.user.username}")
            
            # Convert to list and sort by priority score (calculated in Python)
            user_tasks = list(user_tasks)
            user_tasks.sort(key=lambda x: x.get_moscow_details()['score'], reverse=True)
            
            # Separate tasks by calculated priority
            high_priority_tasks = [task for task in user_tasks if task.get_moscow_details()['score'] >= 400]
            medium_priority_tasks = [task for task in user_tasks if 200 <= task.get_moscow_details()['score'] < 400]
            low_priority_tasks = [task for task in user_tasks if task.get_moscow_details()['score'] < 200]
            
            context = {
                'must_do_tasks': high_priority_tasks,
                'should_do_tasks': medium_priority_tasks,
                'could_do_tasks': low_priority_tasks,
                'wont_do_tasks': [],
                'scheduled_tasks': [],
                'daily_schedule': None,
                'has_schedule': False,
                'source': 'direct',
                'today': today,
                'all_tasks_count': len(user_tasks),
                'selected_task': selected_task,
                'selected_duration': selected_duration,
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
