from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from tasks.models import Task
from django.contrib.auth.models import User
from django.db import connection


@login_required
def analytics_dashboard(request):
    """Enhanced analytics dashboard view"""
    user = request.user
    user_tasks = Task.objects.filter(user=user)
    
    # Current month data
    now = timezone.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    # Basic statistics
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(status='done').count()
    in_progress_tasks = user_tasks.filter(status='in_progress').count()
    overdue_tasks = user_tasks.filter(
        due_date__lt=now,
        status__in=['todo', 'in_progress']
    ).count()
    
    # Monthly comparison
    current_month_completed = user_tasks.filter(
        status='done',
        updated_at__gte=current_month_start
    ).count()
    
    last_month_completed = user_tasks.filter(
        status='done',
        updated_at__gte=last_month_start,
        updated_at__lt=current_month_start
    ).count()
    
    # Calculate percentage changes
    def calculate_percentage_change(current, previous):
        if previous == 0:
            return "+100%" if current > 0 else "0%"
        change = ((current - previous) / previous) * 100
        return f"{'+' if change >= 0 else ''}{change:.0f}%"
    
    # Priority distribution
    priority_distribution = user_tasks.values('priority').annotate(
        count=Count('id')
    ).order_by('priority')
    
    # User performance (mock data for individual user)
    user_performance = [
        {
            'name': f"{user.first_name} {user.last_name}" if user.first_name else user.username,
            'initials': f"{user.first_name[0] if user.first_name else user.username[0]}{user.last_name[0] if user.last_name else ''}",
            'tasks_completed': completed_tasks,
            'rank': 1
        }
    ]
    
    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks, 
        'in_progress_tasks': in_progress_tasks,
        'overdue_tasks': overdue_tasks,
        'current_month_completed': current_month_completed,
        'last_month_completed': last_month_completed,
        'total_change': calculate_percentage_change(total_tasks, total_tasks - 10),  # Mock previous data
        'completed_change': calculate_percentage_change(current_month_completed, last_month_completed),
        'in_progress_change': calculate_percentage_change(in_progress_tasks, in_progress_tasks - 3),
        'overdue_change': calculate_percentage_change(overdue_tasks, overdue_tasks + 2),
        'priority_distribution': priority_distribution,
        'user_performance': user_performance,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def analytics_api(request):
    """API endpoint for analytics data"""
    user = request.user
    user_tasks = Task.objects.filter(user=user)
    
    # Time range filter
    time_range = request.GET.get('range', '30')  # days
    try:
        days = int(time_range)
    except ValueError:
        days = 30
    
    start_date = timezone.now() - timedelta(days=days)
    filtered_tasks = user_tasks.filter(created_at__gte=start_date)
    
    # Task completion over time (based on updated_at for completed tasks)
    completion_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        completed_count = user_tasks.filter(
            status='done',
            updated_at__date=date.date()
        ).count()
        completion_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'completed': completed_count
        })
    
    # Task distribution by status
    status_distribution = dict(
        user_tasks.values('status').annotate(count=Count('id')).values_list('status', 'count')
    )
    
    # Task distribution by priority
    priority_distribution = dict(
        user_tasks.values('priority').annotate(count=Count('id')).values_list('priority', 'count')
    )
    
    # Task distribution by category
    category_distribution = list(
        user_tasks.exclude(category__isnull=True)
        .values('category__name', 'category__color')
        .annotate(count=Count('id'))
    )
    
    # Productivity metrics
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(status='done').count()
    overdue_tasks = user_tasks.filter(
        due_date__lt=timezone.now(),
        status__in=['todo', 'in_progress']
    ).count()
    
    # Average completion time (using creation to last update for done tasks)
    completed_with_times = user_tasks.filter(status='done')
    
    avg_completion_time = None
    if completed_with_times.exists():
        total_time = sum([
            (task.updated_at - task.created_at).total_seconds()
            for task in completed_with_times
        ])
        avg_completion_time = total_time / completed_with_times.count() / 3600  # hours
    
    analytics_data = {
        'overview': {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'overdue_tasks': overdue_tasks,
            'avg_completion_time': round(avg_completion_time, 2) if avg_completion_time else None
        },
        'completion_trend': completion_data,
        'status_distribution': status_distribution,
        'priority_distribution': priority_distribution,
        'category_distribution': category_distribution,
        'time_range': days
    }
    
    return JsonResponse(analytics_data)


@login_required
def system_status(request):
    """System status page for debugging"""
    user = request.user
    
    # Get database info
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM auth_user")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tasks_task")
        task_count = cursor.fetchone()[0]
    
    # User's tasks
    user_tasks = Task.objects.filter(user=user).count()
    
    context = {
        'user': user,
        'system_info': {
            'total_users': user_count,
            'total_tasks': task_count,
            'user_tasks': user_tasks,
            'is_authenticated': user.is_authenticated,
            'session_key': request.session.session_key,
        }
    }
    
    return render(request, 'debug/status.html', context)
