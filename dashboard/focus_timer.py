from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from tasks.models import Task
from django.utils import timezone
from datetime import timedelta

@login_required
def focus_timer(request):
    """Focus Timer view using Pomodoro technique"""
    
    # Get today's tasks for focus session
    today = timezone.now().date()
    
    # Priority-based task selection for 1-3-5 method
    big_tasks = Task.objects.filter(
        user=request.user,
        priority='urgent',
        status__in=['todo', 'in_progress']
    ).order_by('due_date')[:1]
    
    medium_tasks = Task.objects.filter(
        user=request.user,
        priority='high',
        status__in=['todo', 'in_progress']
    ).order_by('due_date')[:3]
    
    small_tasks = Task.objects.filter(
        user=request.user,
        priority__in=['medium', 'low'],
        status__in=['todo', 'in_progress']
    ).order_by('due_date')[:5]
    
    context = {
        'big_tasks': big_tasks,
        'medium_tasks': medium_tasks,
        'small_tasks': small_tasks,
        'today': today,
    }
    
    return render(request, 'dashboard/focus_timer.html', context)
