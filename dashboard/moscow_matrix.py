from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from tasks.models import Task
from django.db.models import Count
from priority_analyzer.services import MoSCoWPriorityPlanner
from priority_analyzer.signals import MoSCoWCacheService

@login_required
def moscow_matrix(request):
    """MoSCoW Matrix view for prioritizing tasks with deterministic priority calculation"""
    
    # Get all active tasks for the user
    all_tasks = Task.objects.filter(
        user=request.user,
        status__in=['todo', 'in_progress']
    ).order_by('due_date', 'created_at')
    
    # Use cached MoSCoW analysis
    result = MoSCoWCacheService.get_moscow_analysis(request.user)
    
    # Create task objects with analysis details
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
    
    # Categorize tasks by their calculated priority
    must_have_tasks = []
    should_have_tasks = []
    could_have_tasks = []
    wont_have_tasks = []
    
    for task in all_tasks:
        details = task_details.get(task.id, {})
        
        # Add analysis details to task object for template display
        task.moscow_category = details.get('category', 'should')
        task.moscow_score = details.get('score', 30)
        task.moscow_task_type = details.get('task_type', 'Regular coursework')
        task.moscow_reasoning = details.get('reasoning', 'Default classification')
        task.moscow_due_in_days = details.get('due_in_days')
        
        # Categorize tasks
        if task.moscow_category == 'must':
            must_have_tasks.append(task)
        elif task.moscow_category == 'should':
            should_have_tasks.append(task)
        elif task.moscow_category == 'could':
            could_have_tasks.append(task)
        else:  # 'wont'
            wont_have_tasks.append(task)
    
    # Sort each category by score (highest first), then by due date
    def sort_tasks(task_list):
        return sorted(task_list, key=lambda x: (
            -x.moscow_score,  # Higher scores first
            x.moscow_due_in_days if x.moscow_due_in_days is not None else float('inf'),  # Earlier due dates first
            x.title.casefold()  # Alphabetical tie-breaker
        ))
    
    must_have_tasks = sort_tasks(must_have_tasks)
    should_have_tasks = sort_tasks(should_have_tasks)
    could_have_tasks = sort_tasks(could_have_tasks)
    wont_have_tasks = sort_tasks(wont_have_tasks)
    
    context = {
        'must_have_tasks': must_have_tasks,
        'should_have_tasks': should_have_tasks,
        'could_have_tasks': could_have_tasks,
        'wont_have_tasks': wont_have_tasks,
        'must_have_count': len(must_have_tasks),
        'should_have_count': len(should_have_tasks),
        'could_have_count': len(could_have_tasks),
        'wont_have_count': len(wont_have_tasks),
        'analysis_timestamp': result['generated_at'],
    }
    
    return render(request, 'dashboard/moscow_matrix.html', context)


@login_required
def refresh_moscow_matrix(request):
    """API endpoint to force refresh MoSCoW matrix"""
    if request.method == 'POST':
        result = MoSCoWCacheService.force_refresh_moscow_analysis(request.user)
        
        # Count tasks in each bucket
        counts = {bucket: len(tasks) for bucket, tasks in result['buckets'].items()}
        
        return JsonResponse({
            'success': True,
            'message': 'MoSCoW matrix refreshed successfully',
            'counts': counts,
            'timestamp': result['generated_at']
        })
    
    return JsonResponse({'success': False, 'message': 'Only POST requests allowed'})
