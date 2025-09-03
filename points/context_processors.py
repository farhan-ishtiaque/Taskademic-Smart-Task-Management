from .services import PointsService


def points_context(request):
    """Add points data to all templates"""
    if request.user.is_authenticated:
        user_level = PointsService.get_or_create_user_level(request.user)
        return {
            'user_points': {
                'level': user_level.current_level,
                'level_name': user_level.level_name,
                'total_points': user_level.total_points,
                'streak_days': user_level.streak_days,
                'progress_percentage': user_level.level_progress_percentage,
            }
        }
    return {}
