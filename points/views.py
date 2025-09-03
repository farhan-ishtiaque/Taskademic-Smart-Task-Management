from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import UserLevel, PointTransaction, DailyActivity, Achievement, UserAchievement
from .services import PointsService


@login_required
def leaderboard_view(request):
    """Display user leaderboard"""
    # Get all users by level and points in descending order
    all_users = UserLevel.objects.select_related('user').order_by(
        '-current_level', '-total_points'
    )
    
    # Add ranking to each user
    ranked_users = []
    for index, user_level in enumerate(all_users, 1):
        user_level.rank = index
        ranked_users.append(user_level)
    
    # Get current user's position
    user_level = PointsService.get_or_create_user_level(request.user)
    user_position = UserLevel.objects.filter(
        total_points__gt=user_level.total_points
    ).count() + 1
    
    context = {
        'ranked_users': ranked_users,
        'user_level': user_level,
        'user_position': user_position,
    }
    return render(request, 'points/leaderboard.html', context)


@login_required
def profile_view(request):
    """Display user's point profile and achievements"""
    stats = PointsService.get_user_stats(request.user)
    
    # Get weekly progress
    week_ago = timezone.now().date() - timedelta(days=7)
    weekly_activities = DailyActivity.objects.filter(
        user=request.user,
        date__gte=week_ago
    ).order_by('date')
    
    # Calculate weekly stats
    weekly_points = sum(activity.points_earned for activity in weekly_activities)
    weekly_completion_rates = [activity.completion_rate for activity in weekly_activities]
    avg_completion_rate = sum(weekly_completion_rates) / len(weekly_completion_rates) if weekly_completion_rates else 0
    
    context = {
        **stats,
        'weekly_activities': weekly_activities,
        'weekly_points': weekly_points,
        'avg_completion_rate': avg_completion_rate,
    }
    return render(request, 'points/profile.html', context)


@login_required
def achievements_view(request):
    """Display all achievements and user progress"""
    all_achievements = Achievement.objects.filter(is_active=True).order_by('criteria_value')
    user_achievements = UserAchievement.objects.filter(user=request.user).values_list('achievement_id', flat=True)
    
    # Categorize achievements
    achievements_data = []
    for achievement in all_achievements:
        is_earned = achievement.id in user_achievements
        progress = 0
        
        if not is_earned:
            # Calculate progress towards achievement
            user_level = PointsService.get_or_create_user_level(request.user)
            
            if achievement.criteria_type == 'streak':
                progress = min(100, (user_level.streak_days / achievement.criteria_value) * 100)
            elif achievement.criteria_type == 'level':
                progress = min(100, (user_level.current_level / achievement.criteria_value) * 100)
            elif achievement.criteria_type == 'total_points':
                progress = min(100, (user_level.total_points / achievement.criteria_value) * 100)
            elif achievement.criteria_type == 'tasks_completed':
                from tasks.models import Task
                completed_count = Task.objects.filter(user=request.user, completed=True).count()
                progress = min(100, (completed_count / achievement.criteria_value) * 100)
        
        achievements_data.append({
            'achievement': achievement,
            'is_earned': is_earned,
            'progress': progress
        })
    
    context = {
        'achievements_data': achievements_data,
        'total_earned': len(user_achievements),
        'total_available': len(all_achievements),
    }
    return render(request, 'points/achievements.html', context)


@login_required
@require_http_methods(["GET"])
def user_stats_api(request):
    """API endpoint for user stats"""
    stats = PointsService.get_user_stats(request.user)
    
    data = {
        'level': {
            'current_level': stats['level'].current_level,
            'level_name': stats['level'].level_name,
            'total_points': stats['level'].total_points,
            'points_to_next_level': stats['level'].points_to_next_level,
            'progress_percentage': stats['level'].level_progress_percentage,
            'streak_days': stats['level'].streak_days,
            'longest_streak': stats['level'].longest_streak,
        },
        'recent_transactions': [
            {
                'points': t.points,
                'type': t.get_transaction_type_display(),
                'description': t.description,
                'date': t.created_at.isoformat(),
            } for t in stats['recent_transactions']
        ],
        'achievements_count': len(stats['achievements']),
        'total_achievements': stats['total_achievements'],
    }
    
    return JsonResponse(data)


def points_widget_data(request):
    """Get points widget data for dashboard"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    user_level = PointsService.get_or_create_user_level(request.user)
    
    # Get today's activity
    today = timezone.now().date()
    today_activity = DailyActivity.objects.filter(user=request.user, date=today).first()
    
    # Get recent points (last 24 hours)
    yesterday = timezone.now() - timedelta(hours=24)
    recent_points = PointTransaction.objects.filter(
        user=request.user,
        created_at__gte=yesterday
    ).aggregate(total=Sum('points'))['total'] or 0
    
    data = {
        'level': user_level.current_level,
        'level_name': user_level.level_name,
        'total_points': user_level.total_points,
        'progress_percentage': user_level.level_progress_percentage,
        'streak_days': user_level.streak_days,
        'recent_points': recent_points,
        'today_completion_rate': today_activity.completion_rate if today_activity else 0,
    }
    
    return JsonResponse(data)
