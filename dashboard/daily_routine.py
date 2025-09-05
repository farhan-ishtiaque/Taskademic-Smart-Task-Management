from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from tasks.models import Task
from datetime import datetime, timedelta
from priority_analyzer.signals import MoSCoWCacheService
from .models import DailySchedule, ScheduledTask

@login_required
def daily_routine(request):
    """Daily routine view for personal task management"""
    today = timezone.now().date()
    
    # Get today's schedule if it exists
    today_schedule = None
    scheduled_tasks = []
    schedule_type = None
    try:
        # Get the latest schedule for today (in case multiple exist)
        today_schedule = DailySchedule.objects.filter(
            user=request.user, 
            date=today
        ).order_by('-generation_timestamp').first()
        
        if today_schedule:
            # Get all scheduled tasks for today first
            all_scheduled_tasks = ScheduledTask.objects.filter(
                user=request.user,
                scheduled_date=today
            ).select_related('task', 'time_block').order_by('start_time')
            
            print(f"DEBUG: Found {all_scheduled_tasks.count()} total scheduled tasks for {today}")
            
            # Determine the primary schedule type
            if all_scheduled_tasks.exists():
                schedule_types = set(all_scheduled_tasks.values_list('schedule_type', flat=True))
                print(f"DEBUG: Schedule types found: {schedule_types}")
                
                if 'ai' in schedule_types:
                    schedule_type = 'ai'
                    # Show only AI generated tasks
                    scheduled_tasks = all_scheduled_tasks.filter(schedule_type='ai')
                    print(f"DEBUG: Using AI schedule with {scheduled_tasks.count()} tasks")
                elif 'custom' in schedule_types:
                    schedule_type = 'custom'
                    # Show only custom tasks
                    scheduled_tasks = all_scheduled_tasks.filter(schedule_type='custom')
                    print(f"DEBUG: Using custom schedule with {scheduled_tasks.count()} tasks")
                else:
                    # Fallback - show all tasks
                    schedule_type = 'mixed'
                    scheduled_tasks = all_scheduled_tasks
                    print(f"DEBUG: Using mixed schedule with {scheduled_tasks.count()} tasks")
            else:
                print(f"DEBUG: No scheduled tasks found for today")
        else:
            print(f"DEBUG: No DailySchedule found for {today}")
            
    except Exception as e:
        print(f"DEBUG: Error getting today's schedule: {e}")
        pass
    
    # Get latest schedule (within last 7 days) if today's doesn't exist
    latest_schedule = None
    latest_scheduled_tasks = []
    if not today_schedule:
        try:
            latest_schedule = DailySchedule.objects.filter(
                user=request.user,
                date__gte=today - timedelta(days=7)
            ).order_by('-date').first()
            
            if latest_schedule:
                latest_scheduled_tasks = ScheduledTask.objects.filter(
                    user=request.user,
                    scheduled_date=latest_schedule.date
                ).select_related('task', 'time_block').order_by('start_time')
        except:
            pass
    
    # Get overdue tasks - personal tasks only
    overdue_tasks = Task.objects.filter(
        user=request.user,
        team__isnull=True,  # Exclude team tasks
        due_date__date__lt=today,
        status__in=['todo', 'in_progress']
    ).order_by('due_date')
    
    # Get MoSCoW analysis for overdue tasks
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
    
    # Apply MoSCoW analysis to overdue tasks
    def apply_moscow_analysis(task_list):
        for task in task_list:
            details = task_details.get(task.id, {})
            task.moscow_category = details.get('category', 'should')
            task.moscow_score = details.get('score', 30)
            task.moscow_task_type = details.get('task_type', 'Regular coursework')
            task.moscow_reasoning = details.get('reasoning', 'Default classification')
            task.moscow_due_in_days = details.get('due_in_days')
        return task_list
    
    overdue_tasks = apply_moscow_analysis(list(overdue_tasks))
    
    context = {
        'today': today,
        'today_schedule': today_schedule,
        'scheduled_tasks': scheduled_tasks,
        'schedule_type': schedule_type,  # Add schedule type for consistency
        'latest_schedule': latest_schedule,
        'latest_scheduled_tasks': latest_scheduled_tasks,
        'overdue_tasks': overdue_tasks,
    }
    
    return render(request, 'dashboard/daily_routine.html', context)
