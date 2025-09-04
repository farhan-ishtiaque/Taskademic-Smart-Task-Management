from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from tasks.models import Task
from datetime import datetime, timedelta

@login_required
def daily_routine(request):
    """Daily routine view for personal task management"""
    today = timezone.now().date()
    
    # Get today's tasks - personal tasks only
    todays_tasks = Task.objects.filter(
        user=request.user,
        team__isnull=True,  # Exclude team tasks
        due_date__date=today
    ).order_by('priority', 'created_at')
    
    # Get upcoming tasks (next 7 days) - personal tasks only
    next_week = today + timedelta(days=7)
    upcoming_tasks = Task.objects.filter(
        user=request.user,
        team__isnull=True,  # Exclude team tasks
        due_date__date__gt=today,
        due_date__date__lte=next_week
    ).order_by('due_date', 'priority')
    
    # Get overdue tasks - personal tasks only
    overdue_tasks = Task.objects.filter(
        user=request.user,
        team__isnull=True,  # Exclude team tasks
        due_date__date__lt=today,
        status__in=['todo', 'in_progress']
    ).order_by('due_date')
    
    context = {
        'todays_tasks': todays_tasks,
        'upcoming_tasks': upcoming_tasks,
        'overdue_tasks': overdue_tasks,
        'today': today,
    }
    
    return render(request, 'dashboard/daily_routine.html', context)
