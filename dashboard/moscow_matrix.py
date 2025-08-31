from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from tasks.models import Task
from django.db.models import Count

@login_required
def moscow_matrix(request):
    """MoScow Matrix view for prioritizing tasks"""
    
    # Get tasks grouped by MoScow categories
    must_have_tasks = Task.objects.filter(
        user=request.user,
        priority='urgent',
        status__in=['todo', 'in_progress']
    ).order_by('created_at')
    
    should_have_tasks = Task.objects.filter(
        user=request.user,
        priority='high',
        status__in=['todo', 'in_progress']
    ).order_by('created_at')
    
    could_have_tasks = Task.objects.filter(
        user=request.user,
        priority='medium',
        status__in=['todo', 'in_progress']
    ).order_by('created_at')
    
    wont_have_tasks = Task.objects.filter(
        user=request.user,
        priority='low',
        status__in=['todo', 'in_progress']
    ).order_by('created_at')
    
    context = {
        'must_have_tasks': must_have_tasks,
        'should_have_tasks': should_have_tasks,
        'could_have_tasks': could_have_tasks,
        'wont_have_tasks': wont_have_tasks,
        'must_have_count': must_have_tasks.count(),
        'should_have_count': should_have_tasks.count(),
        'could_have_count': could_have_tasks.count(),
        'wont_have_count': wont_have_tasks.count(),
    }
    
    return render(request, 'dashboard/moscow_matrix.html', context)
