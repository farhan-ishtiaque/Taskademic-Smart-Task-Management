from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import timedelta, datetime, date
from tasks.models import Task, TimeBlock
from .daily_routine import daily_routine
from priority_analyzer.signals import MoSCoWCacheService
from .moscow_matrix import moscow_matrix
from .focus_timer import focus_timer
from .models import ScheduledTask, DailySchedule
from .ai_scheduler import DeepSeekSchedulerService
import json


@login_required
def dashboard_home(request):
    """Main dashboard view"""
    user = request.user
    
    # Get task statistics - PERSONAL TASKS ONLY (exclude team tasks)
    user_tasks = Task.objects.filter(user=user, team__isnull=True)
    
    # Tasks assigned to me (includes both personal and team tasks assigned to user)
    assigned_tasks = Task.objects.filter(assigned_to=user)
    
    # Recent tasks (last 7 days) - personal tasks + tasks assigned to me
    recent_tasks = Task.objects.filter(
        Q(user=user, team__isnull=True) | Q(assigned_to=user),
        created_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-created_at')[:5]
    
    # Upcoming tasks (next 7 days) - personal tasks + tasks assigned to me
    upcoming_tasks = Task.objects.filter(
        Q(user=user, team__isnull=True) | Q(assigned_to=user),
        due_date__gte=timezone.now(),
        due_date__lte=timezone.now() + timedelta(days=7),
        status__in=['todo', 'in_progress']
    ).order_by('due_date')[:5]
    
    # Overdue tasks - personal tasks + tasks assigned to me
    overdue_tasks = Task.objects.filter(
        Q(user=user, team__isnull=True) | Q(assigned_to=user),
        due_date__lt=timezone.now(),
        status__in=['todo', 'in_progress']
    ).order_by('due_date')[:5]
    
    # Get MoSCoW analysis for tasks
    from priority_analyzer.signals import MoSCoWCacheService
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
    
    # Apply MoSCoW analysis to task lists
    def apply_moscow_analysis(task_list):
        for task in task_list:
            details = task_details.get(task.id, {})
            task.moscow_category = details.get('category', 'should')
            task.moscow_score = details.get('score', 30)
            task.moscow_task_type = details.get('task_type', 'Regular coursework')
            task.moscow_reasoning = details.get('reasoning', 'Default classification')
            task.moscow_due_in_days = details.get('due_in_days')
        return task_list
    
    recent_tasks = apply_moscow_analysis(list(recent_tasks))
    upcoming_tasks = apply_moscow_analysis(list(upcoming_tasks))
    overdue_tasks = apply_moscow_analysis(list(overdue_tasks))
    assigned_tasks_list = apply_moscow_analysis(list(assigned_tasks.filter(status__in=['todo', 'in_progress', 'review'])[:5]))
    
    # Task completion rate (based on personal tasks only)
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(status='done').count()
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Tasks by status
    task_stats = {
        'total': total_tasks,
        'assigned_to_me': assigned_tasks.filter(status__in=['todo', 'in_progress', 'review']).count(),  # Active assigned tasks (including review)
        'completed': completed_tasks,
        'in_progress': user_tasks.filter(status='in_progress').count(),
        'todo': user_tasks.filter(status='todo').count(),
        'overdue': len(overdue_tasks),  # Fixed: use len() for list instead of count()
        'completion_rate': round(completion_rate, 1)
    }
    
    # Tasks by priority (now using MoSCoW categories)
    moscow_stats = {'must': 0, 'should': 0, 'could': 0, 'wont': 0}
    for task_id, details in task_details.items():
        if Task.objects.filter(id=task_id, user=user, team__isnull=True).exists():
            category = details.get('category', 'should')
            moscow_stats[category] = moscow_stats.get(category, 0) + 1
    
    context = {
        'task_stats': task_stats,
        'priority_stats': moscow_stats,  # Now using MoSCoW categories
        'recent_tasks': recent_tasks,
        'upcoming_tasks': upcoming_tasks,
        'overdue_tasks': overdue_tasks,
        'assigned_tasks': assigned_tasks_list,
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def settings_view(request):
    """Settings page"""
    if request.method == 'POST':
        # Handle profile update
        user = request.user
        
        # Get form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        
        # Note: Server timezone (Asia/Dhaka) is used for calendar sync
        
        # Validate email
        if email and email != user.email:
            from django.contrib.auth.models import User
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, 'This email is already in use by another account.')
                return redirect('dashboard:settings')
        
        # Update user fields
        user.first_name = first_name
        user.last_name = last_name
        if email:
            user.email = email
        
        try:
            user.save()
            messages.success(request, 'Profile updated successfully!')
        except Exception as e:
            messages.error(request, 'Error updating profile. Please try again.')
        
        return redirect('dashboard:settings')
    
    return render(request, 'dashboard/settings.html')


@login_required
def daily_schedule_home(request):
    """Main daily schedule view"""
    today = timezone.now().date()
    
    # Get user's time blocks
    time_blocks = TimeBlock.objects.filter(user=request.user, is_available=True)
    
    # Get recent schedules
    recent_schedules = DailySchedule.objects.filter(
        user=request.user,
        date__gte=today - timedelta(days=7)
    ).order_by('-date')[:5]
    
    # Get today's schedule if it exists
    today_schedule = None
    today_tasks = []
    try:
        today_schedule = DailySchedule.objects.get(user=request.user, date=today)
        today_tasks = ScheduledTask.objects.filter(
            user=request.user,
            scheduled_date=today
        ).order_by('start_time')
    except DailySchedule.DoesNotExist:
        pass
    
    context = {
        'time_blocks': time_blocks,
        'recent_schedules': recent_schedules,
        'today_schedule': today_schedule,
        'today_tasks': today_tasks,
        'today': today,
    }
    
    return render(request, 'dashboard/daily_schedule.html', context)


@login_required
def manage_time_blocks(request):
    """Manage user's time blocks"""
    from tasks.models import TimeBlock
    from datetime import datetime, timedelta
    
    if request.method == 'POST':
        # Handle form submission
        day_of_week = request.POST.get('day_of_week')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        apply_weekdays = request.POST.get('apply_all_weekdays')
        apply_weekend = request.POST.get('apply_all_weekend')
        
        try:
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            
            if start_time_obj >= end_time_obj:
                messages.error(request, 'End time must be after start time')
                return redirect('dashboard:manage_time_blocks')
            
            # Determine which days to apply to
            days_to_apply = []
            days_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            if apply_weekdays:
                days_to_apply = [0, 1, 2, 3, 4]  # Monday to Friday
            elif apply_weekend:
                days_to_apply = [5, 6]  # Saturday and Sunday
            else:
                days_to_apply = [days_map[day_of_week]]
            
            created_count = 0
            for day_num in days_to_apply:
                # Check for conflicts
                existing_blocks = TimeBlock.objects.filter(
                    user=request.user,
                    day_of_week=day_num,
                    is_available=True
                )
                
                has_conflict = False
                for block in existing_blocks:
                    if not (end_time_obj <= block.start_time or start_time_obj >= block.end_time):
                        has_conflict = True
                        break
                
                if not has_conflict:
                    TimeBlock.objects.create(
                        user=request.user,
                        day_of_week=day_num,
                        start_time=start_time_obj,
                        end_time=end_time_obj,
                        is_available=True
                    )
                    created_count += 1
            
            if created_count > 0:
                messages.success(request, f'Successfully added {created_count} time block(s)')
            else:
                messages.warning(request, 'No time blocks were added due to conflicts')
                
        except Exception as e:
            messages.error(request, f'Error adding time block: {str(e)}')
        
        return redirect('dashboard:manage_time_blocks')
    
    # GET request - display the page
    time_blocks = TimeBlock.objects.filter(user=request.user, is_available=True).order_by('day_of_week', 'start_time')
    
    # Prepare days of week with time blocks
    today = timezone.now().date()
    days_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    days_of_week = []
    
    for i, day_name in enumerate(days_names):
        # Calculate the date for this day in the current week
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        day_date = monday + timedelta(days=i)
        
        # Get time blocks for this day
        day_blocks = time_blocks.filter(day_of_week=i)
        
        days_of_week.append({
            'name': day_name,
            'date': day_date,
            'time_blocks': day_blocks
        })

    # Prepare time_blocks_by_day for template
    time_blocks_by_day = {}
    day_hours = {}
    
    for i, day_name in enumerate(days_names):
        day_blocks = time_blocks.filter(day_of_week=i)
        time_blocks_by_day[day_name] = list(day_blocks)
        
        # Calculate total hours for this day
        total_hours = 0
        for block in day_blocks:
            # Calculate duration in hours
            start_datetime = datetime.combine(datetime.today(), block.start_time)
            end_datetime = datetime.combine(datetime.today(), block.end_time)
            
            # Handle overnight blocks (end time next day)
            if end_datetime <= start_datetime:
                end_datetime += timedelta(days=1)
            
            duration = end_datetime - start_datetime
            total_hours += duration.total_seconds() / 3600  # Convert to hours
        
        day_hours[day_name] = round(total_hours, 1)
    
    context = {
        'days_of_week': days_of_week,
        'time_blocks_by_day': time_blocks_by_day,
        'time_blocks': time_blocks,  # Add this for template condition
        'day_hours': day_hours,  # Add calculated hours

    }
    
    return render(request, 'dashboard/time_blocks.html', context)


@login_required
def add_time_block(request):
    """Add a new time block"""
    if request.method == 'POST':
        day_of_week = request.POST.get('day_of_week')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        try:
            # Convert day name to number
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            day_number = days.index(day_of_week)
            
            # Check for conflicts
            existing_blocks = TimeBlock.objects.filter(
                user=request.user,
                day_of_week=day_number,
                is_available=True
            )
            
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            
            # Check for overlaps
            for block in existing_blocks:
                if not (end_time_obj <= block.start_time or start_time_obj >= block.end_time):
                    messages.error(request, f'Time block conflicts with existing block: {block.start_time}-{block.end_time}')
                    return redirect('dashboard:manage_time_blocks')
            
            # Create the time block
            TimeBlock.objects.create(
                user=request.user,
                day_of_week=day_number,
                start_time=start_time_obj,
                end_time=end_time_obj,
                is_available=True
            )
            
            messages.success(request, 'Time block added successfully!')
            
        except Exception as e:
            messages.error(request, f'Error adding time block: {str(e)}')
    
    return redirect('dashboard:manage_time_blocks')


@login_required
def delete_time_block(request, block_id):
    """Delete a time block"""
    if request.method == 'POST':
        try:
            from tasks.models import TimeBlock
            time_block = TimeBlock.objects.get(id=block_id, user=request.user)
            time_block.delete()
            messages.success(request, 'Time block deleted successfully!')
        except TimeBlock.DoesNotExist:
            messages.error(request, 'Time block not found')
        except Exception as e:
            messages.error(request, f'Error deleting time block: {str(e)}')
    
    return redirect('dashboard:manage_time_blocks')


@login_required 
def edit_time_block(request, block_id):
    """Edit a time block"""
    if request.method == 'POST':
        try:
            from tasks.models import TimeBlock
            time_block = TimeBlock.objects.get(id=block_id, user=request.user)
            
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            
            if start_time_obj >= end_time_obj:
                messages.error(request, 'End time must be after start time')
                return redirect('dashboard:manage_time_blocks')
            
            # Check for conflicts with other blocks (excluding current one)
            existing_blocks = TimeBlock.objects.filter(
                user=request.user,
                day_of_week=time_block.day_of_week,
                is_available=True
            ).exclude(id=block_id)
            
            for block in existing_blocks:
                if not (end_time_obj <= block.start_time or start_time_obj >= block.end_time):
                    messages.error(request, f'Time block conflicts with existing block: {block.start_time}-{block.end_time}')
                    return redirect('dashboard:manage_time_blocks')
            
            # Update the time block
            time_block.start_time = start_time_obj
            time_block.end_time = end_time_obj
            time_block.save()
            
            messages.success(request, 'Time block updated successfully!')
            
        except TimeBlock.DoesNotExist:
            messages.error(request, 'Time block not found')
        except Exception as e:
            messages.error(request, f'Error updating time block: {str(e)}')
    
    return redirect('dashboard:manage_time_blocks')





@login_required
def generate_schedule(request):
    """Generate AI-powered daily schedule"""
    if request.method == 'POST':
        target_date_str = request.POST.get('target_date')
        
        try:
            # Parse target date
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            
            # Check if schedule already exists
            existing_schedule = DailySchedule.objects.filter(
                user=request.user,
                date=target_date
            ).first()
            
            if existing_schedule:
                # Delete existing schedule and regenerate
                ScheduledTask.objects.filter(user=request.user, scheduled_date=target_date).delete()
                existing_schedule.delete()
            
            # Initialize AI scheduler
            scheduler = DeepSeekSchedulerService()
            
            try:
                # Generate schedule (now includes intelligent fallback)
                daily_schedule, scheduled_tasks = scheduler.generate_daily_schedule(request.user, target_date)
                
                # Prepare success message
                if hasattr(daily_schedule, 'ai_response') and 'Fallback scheduling' in daily_schedule.ai_response:
                    success_message = f'AI scheduling unavailable (rate limit), used intelligent fallback. Generated optimized schedule for {len(scheduled_tasks)} tasks.'
                else:
                    success_message = f'Successfully generated AI-powered schedule for {target_date.strftime("%B %d, %Y")}! Scheduled {len(scheduled_tasks)} tasks with focus timer support.'
                
                # Return JSON response for AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': success_message,
                        'redirect_url': f'/dashboard/schedule/view/{target_date.year}/{target_date.month}/{target_date.day}/'
                    })
                else:
                    messages.success(request, success_message)
                    return redirect('dashboard:view_schedule', year=target_date.year, month=target_date.month, day=target_date.day)
                
            except Exception as e:
                error_message = f'Error generating schedule: {str(e)}'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': error_message
                    })
                else:
                    messages.error(request, error_message)
        
        except Exception as e:
            error_message = f'Error processing request: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_message
                })
            else:
                messages.error(request, error_message)
    
    return redirect('dashboard:daily_routine')


@login_required
def view_schedule(request, year, month, day):
    """View a specific day's schedule"""
    try:
        target_date = datetime(year, month, day).date()
        

        # Try to get the schedule, but don't fail if it doesn't exist
        try:
            schedule = DailySchedule.objects.get(user=request.user, date=target_date)
        except DailySchedule.DoesNotExist:
            # Create a default schedule object with empty values
            schedule = DailySchedule(
                user=request.user,
                date=target_date,
                total_available_minutes=0,
                total_scheduled_minutes=0,
                total_break_minutes=0,
                tasks_count=0,
                moscow_must_count=0,
                moscow_should_count=0,
                moscow_could_count=0,
                ai_response='{}',
            )

        
        # Get scheduled tasks
        scheduled_tasks = ScheduledTask.objects.filter(
            user=request.user,
            scheduled_date=target_date
        ).order_by('start_time')
        

        # Build schedule items from scheduled tasks
        schedule_items = []
        for scheduled_task in scheduled_tasks:
            item = {
                'start_time': scheduled_task.start_time,
                'end_time': scheduled_task.end_time,
                'duration_minutes': scheduled_task.estimated_duration_minutes,
                'task': scheduled_task.task,
                'title': scheduled_task.task.title if scheduled_task.task else "Scheduled Item",
                'description': scheduled_task.task.description if scheduled_task.task else "",
            }
            schedule_items.append(item)
        
        # Add schedule_items to schedule object
        schedule.schedule_items = schedule_items
        

        # Get time blocks for this day
        day_number = target_date.weekday()  # Monday=0, Sunday=6
        time_blocks = TimeBlock.objects.filter(
            user=request.user,
            day_of_week=day_number,
            is_available=True
        ).order_by('start_time')
        

        # Get incomplete tasks to show what could be scheduled
        available_tasks = Task.objects.filter(
            user=request.user,
            status__in=['todo', 'in_progress', 'review']  # All non-completed statuses
        ).order_by('priority', 'due_date')
        
        # Apply MoSCoW analysis to tasks
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
        
        # Apply MoSCoW analysis to available tasks
        available_tasks_list = list(available_tasks)
        for task in available_tasks_list:
            details = task_details.get(task.id, {})
            task.moscow_category = details.get('category', 'should')
            task.moscow_score = details.get('score', 30)
            task.moscow_task_type = details.get('task_type', 'Regular coursework')
            task.moscow_reasoning = details.get('reasoning', 'Default classification')
            task.moscow_due_in_days = details.get('due_in_days')
        
        # Apply MoSCoW analysis to scheduled tasks
        for scheduled_task in scheduled_tasks:
            if scheduled_task.task:
                details = task_details.get(scheduled_task.task.id, {})
                scheduled_task.task.moscow_category = details.get('category', 'should')
                scheduled_task.task.moscow_score = details.get('score', 30)
                scheduled_task.task.moscow_task_type = details.get('task_type', 'Regular coursework')
                scheduled_task.task.moscow_reasoning = details.get('reasoning', 'Default classification')
                scheduled_task.task.moscow_due_in_days = details.get('due_in_days')
        
        # Parse AI response
        ai_analysis = None
        try:
            ai_analysis = json.loads(schedule.ai_response) if hasattr(schedule, 'ai_response') else {}
        except:
            ai_analysis = {}

        # Determine the actual schedule type based on the tasks
        actual_schedule_type = 'custom'  # Default to custom
        if scheduled_tasks.exists():
            # Check what type of tasks we actually have
            schedule_types = scheduled_tasks.values_list('schedule_type', flat=True).distinct()
            if 'ai' in schedule_types:
                actual_schedule_type = 'ai'
            elif 'custom' in schedule_types:
                actual_schedule_type = 'custom'
        
        context = {
            'schedule': schedule,
            'scheduled_tasks': scheduled_tasks,
            'time_blocks': time_blocks,
            'target_date': target_date,
            'ai_analysis': ai_analysis,
            'actual_schedule_type': actual_schedule_type,  # Pass the real schedule type
            'available_tasks': available_tasks_list,
            'has_time_blocks': time_blocks.exists(),
            'has_tasks': len(available_tasks_list) > 0,

        }
        
        return render(request, 'dashboard/view_schedule.html', context)
        
    except Exception as e:
        messages.error(request, f'Error viewing schedule: {str(e)}')
        return redirect('dashboard:daily_schedule_home')


@login_required
@require_http_methods(["POST"])
def mark_task_completed(request, task_id):
    """Mark a scheduled task as completed"""
    try:
        scheduled_task = get_object_or_404(ScheduledTask, id=task_id, user=request.user)
        scheduled_task.is_completed = True
        scheduled_task.save()
        
        # Also mark the original task as completed if specified
        if request.POST.get('complete_original_task') == 'true':
            original_task = scheduled_task.task
            original_task.status = 'done'
            original_task.save()
        
        return JsonResponse({'success': True, 'message': 'Task marked as completed'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def schedule_history(request):
    """View schedule history with filtering and pagination"""
    from django.core.paginator import Paginator
    from django.db.models import Count, Avg, Sum
    
    # Get date filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    days = request.GET.get('days')
    
    # Set default date range
    end_date_obj = timezone.now().date()
    
    if days:
        # Quick filter
        start_date_obj = end_date_obj - timedelta(days=int(days))
    elif start_date and end_date:
        # Custom date range
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        # Default: last 30 days
        start_date_obj = end_date_obj - timedelta(days=30)
    
    # Get schedules
    schedules = DailySchedule.objects.filter(
        user=request.user,
        date__range=[start_date_obj, end_date_obj]
    ).order_by('-date')
    
    # Calculate statistics for each schedule
    for schedule in schedules:
        scheduled_tasks = ScheduledTask.objects.filter(
            user=request.user,
            scheduled_date=schedule.date
        )
        
        completed_tasks = scheduled_tasks.filter(is_completed=True)
        
        schedule.completed_tasks_count = completed_tasks.count()
        schedule.completion_rate = (
            (completed_tasks.count() / scheduled_tasks.count() * 100) 
            if scheduled_tasks.count() > 0 else 0
        )
    
    # Calculate overall statistics
    stats = {
        'total_schedules': schedules.count(),
        'total_tasks_scheduled': sum(s.tasks_count for s in schedules),
        'total_tasks_completed': sum(getattr(s, 'completed_tasks_count', 0) for s in schedules),
        'avg_efficiency': sum(getattr(s, 'completion_rate', 0) for s in schedules) / max(schedules.count(), 1),
        'total_work_hours': sum(s.total_scheduled_minutes for s in schedules) / 60.0,
        'total_pomodoros': sum(
            ScheduledTask.objects.filter(
                user=request.user,
                scheduled_date=s.date
            ).aggregate(total=Sum('pomodoro_sessions'))['total'] or 0
            for s in schedules
        ),
    }
    
    # Pagination
    paginator = Paginator(schedules, 12)  # 12 schedules per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'schedules': page_obj,
        'stats': stats,
        'start_date': start_date_obj,
        'end_date': end_date_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    
    return render(request, 'dashboard/schedule_history.html', context)


@login_required
@require_http_methods(["POST"])
def create_custom_schedule(request):
    """Create a custom schedule with user-defined timing"""
    try:
        data = json.loads(request.body)
        target_date_str = data.get('date')
        schedule_title = data.get('title', 'Custom Schedule')
        tasks_data = data.get('tasks', [])
        schedule_type = data.get('type', 'simple')
        
        # Parse the target date
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        
        if not tasks_data:
            return JsonResponse({'success': False, 'error': 'No tasks selected'})
        
        # Handle both old format (list of IDs) and new format (list of objects)
        if tasks_data and isinstance(tasks_data[0], str):
            # Old format: convert to new format with default timing
            task_ids = tasks_data
            tasks_timing = {}
            for i, task_id in enumerate(task_ids):
                start_hour = 9 + i  # Start from 9 AM, increment by hour
                tasks_timing[task_id] = {
                    'id': task_id,
                    'start_time': f'{start_hour:02d}:00',
                    'duration': 60,
                    'notes': ''
                }
        else:
            # New format: extract task IDs and create timing lookup
            task_ids = [str(task_data['id']) for task_data in tasks_data]
            tasks_timing = {str(task_data['id']): task_data for task_data in tasks_data}
        
        # Get selected tasks
        tasks = Task.objects.filter(
            Q(user=request.user) | Q(assigned_to=request.user),
            id__in=task_ids
        )
        
        if not tasks.exists():
            return JsonResponse({'success': False, 'error': 'No valid tasks found'})
        
        # Create or update daily schedule
        schedule, created = DailySchedule.objects.get_or_create(
            user=request.user,
            date=target_date,
            defaults={
                'tasks_count': len(task_ids),
                'total_scheduled_minutes': 0,
                'total_available_minutes': 0,
                'total_break_minutes': 0,
                'moscow_must_count': 0,
                'moscow_should_count': 0,
                'moscow_could_count': 0,
                'moscow_wont_count': 0,
                'generation_method': 'custom',
                'ai_reasoning': f'Custom schedule: {schedule_title}',
                'ai_prompt_used': f'Custom schedule created: {schedule_title}',
                'ai_response': '{"type": "custom", "method": "manual"}'
            }
        )
        
        # Clear existing scheduled tasks for this date
        ScheduledTask.objects.filter(
            user=request.user,
            scheduled_date=target_date
        ).delete()
        
        # Get or create a default time block for custom schedules
        from tasks.models import TimeBlock
        default_time_block, _ = TimeBlock.objects.get_or_create(
            user=request.user,
            day_of_week=target_date.weekday(),
            start_time=timezone.now().time().replace(hour=9, minute=0, second=0, microsecond=0),
            end_time=timezone.now().time().replace(hour=17, minute=0, second=0, microsecond=0),
            defaults={
                'is_available': True
            }
        )

        # Create scheduled tasks with simple timing
        current_time = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0).time()
        
        # Get or create a default time block for custom schedules
        from tasks.models import TimeBlock
        default_time_block, _ = TimeBlock.objects.get_or_create(
            user=request.user,
            day_of_week=target_date.weekday(),
            start_time=timezone.now().time().replace(hour=9, minute=0, second=0, microsecond=0),
            end_time=timezone.now().time().replace(hour=17, minute=0, second=0, microsecond=0),
            defaults={
                'is_available': True,
                'description': 'Default time block for custom schedules'
            }
        )
        

        total_minutes = 0
        moscow_counts = {'must': 0, 'should': 0, 'could': 0, 'wont': 0}
        
        # Create scheduled tasks with user-defined timing
        for task in tasks:
            task_timing = tasks_timing.get(str(task.id))
            if not task_timing:
                continue
                
            # Parse user-defined start time and duration
            start_time_str = task_timing['start_time']  # Format: "HH:MM"
            duration_minutes = int(task_timing['duration'])
            notes = task_timing.get('notes', '')
            
            # Convert start time string to time object
            start_hour, start_minute = map(int, start_time_str.split(':'))
            start_time = timezone.now().time().replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            
            # Calculate end time based on duration
            end_minutes_total = start_hour * 60 + start_minute + duration_minutes
            end_hour = (end_minutes_total // 60) % 24
            end_minute = end_minutes_total % 60
            end_time = timezone.now().time().replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            
            # Create scheduled task with user-defined timing (no automatic breaks)
            scheduled_task = ScheduledTask.objects.create(
                user=request.user,
                task=task,
                time_block=default_time_block,
                scheduled_date=target_date,
                start_time=start_time,
                end_time=end_time,
                estimated_duration_minutes=duration_minutes,
                pomodoro_sessions=max(1, duration_minutes // 25),  # For focus timer reference
                break_minutes=0,  # No automatic breaks - user decides
                ai_reasoning=f'Custom schedule: {schedule_title}' + (f' - {notes}' if notes else ''),
                priority_score=50.0,  # Default priority score
                schedule_type='custom'  # Mark this as custom schedule
            )
            
            # Update counts
            total_minutes += duration_minutes
            moscow_counts['should'] += 1  # Default to 'should' for custom schedules
        
        # Update schedule totals (no automatic break time)
        schedule.tasks_count = len(task_ids)
        schedule.total_scheduled_minutes = total_minutes
        schedule.total_break_minutes = 0  # No automatic breaks for custom schedules
        schedule.moscow_must_count = moscow_counts['must']
        schedule.moscow_should_count = moscow_counts['should']
        schedule.moscow_could_count = moscow_counts['could']
        schedule.moscow_wont_count = moscow_counts['wont']
        schedule.total_available_minutes = total_minutes  # Just work time, no breaks
        schedule.save()
        
        # Generate schedule URL
        schedule_url = f"/dashboard/schedule/view/{target_date.year}/{target_date.month}/{target_date.day}/"
        
        return JsonResponse({
            'success': True,
            'message': f'Custom schedule created with {len(task_ids)} tasks',
            'schedule_url': schedule_url,
            'tasks_count': len(task_ids),
            'total_minutes': total_minutes
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': f'Error creating custom schedule: {str(e)}',
            'debug': traceback.format_exc()
        })


def onboarding_view(request):
    """Onboarding page for new users"""
    return render(request, 'dashboard/onboarding.html')
