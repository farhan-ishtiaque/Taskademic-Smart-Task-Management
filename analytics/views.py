from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from tasks.models import Task
from django.contrib.auth.models import User


@login_required
def analytics_dashboard(request):
    """Enhanced analytics dashboard view"""
    # Get basic analytics data for initial page load
    user = request.user
    
    # Basic stats - personal tasks only
    total_tasks = Task.objects.filter(user=user, team__isnull=True).count()
    completed_tasks = Task.objects.filter(user=user, team__isnull=True, status='done').count()
    pending_tasks = Task.objects.filter(user=user, team__isnull=True, status__in=['todo', 'in_progress']).count()
    
    # Calculate overdue tasks - personal tasks only
    now = timezone.now()
    overdue_tasks = Task.objects.filter(
        user=user,
        team__isnull=True,  # Exclude team tasks
        due_date__lt=now,
        status__in=['todo', 'in_progress']
    ).count()
    
    # Calculate completion rate
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate': round(completion_rate, 1),
    }
    
    return render(request, 'analytics/dashboard.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_progress(request):
    """Get daily progress data for charts"""
    user = request.user
    days = int(request.GET.get('days', 7))  # Default to 7 days
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    daily_data = []
    current_date = start_date
    
    while current_date <= end_date:
        # Tasks due on this date
        tasks_due = Task.objects.filter(
            user=user,
            due_date__date=current_date
        )
        
        # Tasks completed on this date
        tasks_completed = tasks_due.filter(status='done')
        
        daily_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'day_name': current_date.strftime('%a'),
            'total_due': tasks_due.count(),
            'completed': tasks_completed.count(),
            'percentage': (tasks_completed.count() / tasks_due.count() * 100) if tasks_due.count() > 0 else 0
        })
        
        current_date += timedelta(days=1)
    
    return Response({
        'period': f"{start_date} to {end_date}",
        'daily_progress': daily_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weekly_category_stats(request):
    """Get weekly category completion statistics for pie chart"""
    user = request.user
    week_ago = timezone.now() - timedelta(days=7)
    
    # Get completed tasks in the last week by category
    stats = Task.objects.filter(
        user=user,
        completed_at__gte=week_ago,
        status='done'
    ).values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Calculate total for percentages
    total_completed = sum(item['count'] for item in stats)
    
    # Add percentage and category labels
    category_labels = dict(Task.CATEGORY_CHOICES)
    for item in stats:
        item['label'] = category_labels.get(item['category'], item['category'])
        item['percentage'] = (item['count'] / total_completed * 100) if total_completed > 0 else 0
    
    return Response({
        'period': 'Last 7 days',
        'total_completed': total_completed,
        'category_stats': list(stats)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def priority_breakdown(request):
    """Get task breakdown by MoSCoW priority"""
    user = request.user
    
    priority_data = []
    priority_labels = dict(Task.PRIORITY_CHOICES)
    
    for priority_key, priority_label in Task.PRIORITY_CHOICES:
        total = Task.objects.filter(user=user, priority=priority_key).count()
        completed = Task.objects.filter(user=user, priority=priority_key, status='done').count()
        pending = total - completed
        
        priority_data.append({
            'priority': priority_key,
            'label': priority_label,
            'total': total,
            'completed': completed,
            'pending': pending,
            'completion_rate': (completed / total * 100) if total > 0 else 0
        })
    
    return Response(priority_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def productivity_trends(request):
    """Get productivity trends over time"""
    user = request.user
    days = int(request.GET.get('days', 30))
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    # Weekly aggregation for better visualization
    weekly_data = []
    current_week_start = start_date
    
    while current_week_start <= end_date:
        week_end = min(current_week_start + timedelta(days=6), end_date)
        
        # Tasks completed in this week
        week_completed = Task.objects.filter(
            user=user,
            completed_at__date__gte=current_week_start,
            completed_at__date__lte=week_end,
            status='done'
        ).count()
        
        # Total points earned in this week
        week_points = Task.objects.filter(
            user=user,
            completed_at__date__gte=current_week_start,
            completed_at__date__lte=week_end,
            status='done'
        ).aggregate(total_points=Count('points_awarded'))['total_points'] or 0
        
        weekly_data.append({
            'week_start': current_week_start.strftime('%Y-%m-%d'),
            'week_end': week_end.strftime('%Y-%m-%d'),
            'tasks_completed': week_completed,
            'points_earned': week_points * 10,  # 10 points per completed task
            'week_label': f"Week of {current_week_start.strftime('%b %d')}"
        })
        
        current_week_start = week_end + timedelta(days=1)
    
    return Response({
        'period': f"{start_date} to {end_date}",
        'weekly_trends': weekly_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_points_level(request):
    """Get user points and level information"""
    user = request.user
    profile = user.userprofile
    
    # Calculate points needed for next level
    current_level_points = (profile.level - 1) * 100
    next_level_points = profile.level * 100
    points_to_next_level = next_level_points - profile.total_points
    
    # Recent achievements
    recent_completed = Task.objects.filter(
        user=user,
        status='done',
        completed_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    return Response({
        'total_points': profile.total_points,
        'current_level': profile.level,
        'points_to_next_level': max(0, points_to_next_level),
        'progress_percentage': ((profile.total_points - current_level_points) / 100 * 100),
        'recent_completed_tasks': recent_completed,
        'streak_count': profile.streak_count,
        'preferred_technique': profile.preferred_technique
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def overdue_analysis(request):
    """Analyze overdue tasks patterns"""
    user = request.user
    now = timezone.now()
    
    # Current overdue tasks
    overdue_tasks = Task.objects.filter(
        user=user,
        due_date__lt=now,
        status__in=['todo', 'in_progress']
    )
    
    # Overdue by category
    overdue_by_category = overdue_tasks.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Overdue by priority
    overdue_by_priority = overdue_tasks.values('priority').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Average days overdue
    overdue_days = []
    for task in overdue_tasks:
        days_overdue = (now.date() - task.due_date.date()).days
        overdue_days.append(days_overdue)
    
    avg_days_overdue = sum(overdue_days) / len(overdue_days) if overdue_days else 0
    
    return Response({
        'total_overdue': overdue_tasks.count(),
        'average_days_overdue': round(avg_days_overdue, 1),
        'overdue_by_category': list(overdue_by_category),
        'overdue_by_priority': list(overdue_by_priority),
        'overdue_tasks': [{
            'id': task.id,
            'title': task.title,
            'due_date': task.due_date,
            'days_overdue': (now.date() - task.due_date.date()).days,
            'priority': task.priority,
            'category': task.category
        } for task in overdue_tasks[:10]]  # Limit to 10 most recent
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_api(request):
    """Combined analytics API endpoint for dashboard"""
    user = request.user
    time_range = int(request.GET.get('range', 30))
    
    # Basic overview
    total_tasks = Task.objects.filter(user=user).count()
    completed_tasks = Task.objects.filter(user=user, status='done').count()
    pending_tasks = Task.objects.filter(user=user, status__in=['todo', 'in_progress']).count()
    
    # Calculate overdue tasks
    now = timezone.now()
    overdue_tasks = Task.objects.filter(
        user=user,
        due_date__lt=now,
        status__in=['todo', 'in_progress']
    ).count()
    
    # Calculate completion rate
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Completion trend (last 30 days)
    end_date = now.date()
    start_date = end_date - timedelta(days=time_range-1)
    
    completion_trend = []
    current_date = start_date
    
    while current_date <= end_date:
        completed_on_date = Task.objects.filter(
            user=user,
            completed_at__date=current_date,
            status='done'
        ).count()
        
        completion_trend.append({
            'date': current_date.isoformat(),
            'completed': completed_on_date
        })
        current_date += timedelta(days=1)
    
    # Status distribution
    status_distribution = {}
    for status, label in Task.STATUS_CHOICES:
        count = Task.objects.filter(user=user, status=status).count()
        if count > 0:
            status_distribution[status] = count
    
    # Priority distribution
    priority_distribution = {}
    for priority, label in Task.PRIORITY_CHOICES:
        count = Task.objects.filter(user=user, priority=priority).count()
        if count > 0:
            priority_distribution[priority] = count
    
    # Category distribution
    category_distribution = Task.objects.filter(user=user).values(
        'category'
    ).annotate(count=Count('id')).order_by('-count')
    
    return Response({
        'time_range': time_range,
        'overview': {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'overdue_tasks': overdue_tasks,
            'completion_rate': completion_rate
        },
        'completion_trend': completion_trend,
        'status_distribution': status_distribution,
        'priority_distribution': priority_distribution,
        'category_distribution': list(category_distribution)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_summary(request):
    """Get comprehensive analytics summary"""
    user = request.user
    
    # Basic stats
    total_tasks = Task.objects.filter(user=user).count()
    completed_tasks = Task.objects.filter(user=user, status='done').count()
    pending_tasks = Task.objects.filter(user=user, status__in=['todo', 'in_progress']).count()
    
    # This month stats
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    month_completed = Task.objects.filter(
        user=user,
        status='done',
        completed_at__gte=month_start
    ).count()
    
    month_created = Task.objects.filter(
        user=user,
        created_at__gte=month_start
    ).count()
    
    # User profile data
    profile = user.userprofile
    
    return Response({
        'user_stats': {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        },
        'monthly_stats': {
            'completed_this_month': month_completed,
            'created_this_month': month_created,
            'month_name': now.strftime('%B %Y')
        },
        'gamification': {
            'total_points': profile.total_points,
            'current_level': profile.level,
            'streak_count': profile.streak_count
        },
        'preferences': {
            'preferred_technique': profile.preferred_technique,
            'study_hours_per_day': profile.study_hours_per_day
        }
    })
