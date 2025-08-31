from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from tasks.models import Task
from django.db import connection

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
