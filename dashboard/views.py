from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task
from .daily_routine import daily_routine
from .moscow_matrix import moscow_matrix
from .focus_timer import focus_timer


@login_required
def dashboard_home(request):
    """Main dashboard view"""
    user = request.user
    
    # Get task statistics
    user_tasks = Task.objects.filter(user=user)
    
    # Recent tasks (last 7 days)
    recent_tasks = user_tasks.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-created_at')[:5]
    
    # Upcoming tasks (next 7 days)
    upcoming_tasks = user_tasks.filter(
        due_date__gte=timezone.now(),
        due_date__lte=timezone.now() + timedelta(days=7),
        status__in=['todo', 'in_progress']
    ).order_by('due_date')[:5]
    
    # Overdue tasks
    overdue_tasks = user_tasks.filter(
        due_date__lt=timezone.now(),
        status__in=['todo', 'in_progress']
    ).order_by('due_date')[:5]
    
    # Task completion rate
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(status='done').count()
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Tasks by status
    task_stats = {
        'total': total_tasks,
        'completed': completed_tasks,
        'in_progress': user_tasks.filter(status='in_progress').count(),
        'todo': user_tasks.filter(status='todo').count(),
        'overdue': overdue_tasks.count(),
        'completion_rate': round(completion_rate, 1)
    }
    
    # Tasks by priority
    priority_stats = dict(
        user_tasks.values('priority').annotate(count=Count('id')).values_list('priority', 'count')
    )
    
    context = {
        'task_stats': task_stats,
        'priority_stats': priority_stats,
        'recent_tasks': recent_tasks,
        'upcoming_tasks': upcoming_tasks,
        'overdue_tasks': overdue_tasks,
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def settings_view(request):
    """Settings page"""
    return render(request, 'dashboard/settings.html')


def onboarding_view(request):
    """Onboarding page for new users"""
    return render(request, 'dashboard/onboarding.html')
