from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from tasks.models import Task
from django.db.models import Count

@login_required
def moscow_matrix(request):
    """MoScow Matrix view for prioritizing tasks with automatic priority calculation"""
    
    # Get all active tasks for the user
    all_tasks = Task.objects.filter(
        user=request.user,
        status__in=['todo', 'in_progress']
    ).order_by('due_date', 'created_at')
    
    # Categorize tasks by their auto-calculated priority
    must_have_tasks = []
    should_have_tasks = []
    could_have_tasks = []
    wont_have_tasks = []
    
    for task in all_tasks:
        auto_priority = task.get_auto_priority()
        task.auto_priority = auto_priority  # Add this for template display
        task.priority_score = task.calculate_priority_score()  # Add score for display
        
        if auto_priority == 'must':
            must_have_tasks.append(task)
        elif auto_priority == 'should':
            should_have_tasks.append(task)
        elif auto_priority == 'could':
            could_have_tasks.append(task)
        else:  # 'wont'
            wont_have_tasks.append(task)
    
    # Sort each category by priority score (highest first)
    must_have_tasks.sort(key=lambda x: x.priority_score, reverse=True)
    should_have_tasks.sort(key=lambda x: x.priority_score, reverse=True)
    could_have_tasks.sort(key=lambda x: x.priority_score, reverse=True)
    wont_have_tasks.sort(key=lambda x: x.priority_score, reverse=True)
    
    context = {
        'must_have_tasks': must_have_tasks,
        'should_have_tasks': should_have_tasks,
        'could_have_tasks': could_have_tasks,
        'wont_have_tasks': wont_have_tasks,
        'must_have_count': len(must_have_tasks),
        'should_have_count': len(should_have_tasks),
        'could_have_count': len(could_have_tasks),
        'wont_have_count': len(wont_have_tasks),
    }
    
    return render(request, 'dashboard/moscow_matrix.html', context)
