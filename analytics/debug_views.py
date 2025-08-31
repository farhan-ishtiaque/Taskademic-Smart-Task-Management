from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from tasks.models import Task, Category
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

@login_required
def analytics_debug(request):
    """Debug endpoint to check analytics data issues"""
    user = request.user
    user_tasks = Task.objects.filter(user=user)
    
    debug_info = {
        'user': {
            'username': user.username,
            'is_authenticated': user.is_authenticated,
        },
        'tasks': {
            'total_count': user_tasks.count(),
            'tasks_list': [
                {
                    'title': task.title,
                    'status': task.status,
                    'created_at': task.created_at.isoformat(),
                    'updated_at': task.updated_at.isoformat(),
                } for task in user_tasks[:5]  # First 5 tasks
            ]
        },
        'request_info': {
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT', 'N/A'),
        }
    }
    
    return JsonResponse(debug_info, indent=2)
