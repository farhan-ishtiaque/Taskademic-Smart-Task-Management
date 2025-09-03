from django.utils import timezone
from datetime import datetime, timedelta
from .models import UserLevel, PointTransaction, DailyActivity, Achievement, UserAchievement
import logging

logger = logging.getLogger(__name__)


class PointsService:
    """Service for managing user points and levels"""
    
    # Point values for different actions
    POINTS = {
        'task_complete_low': 5,
        'task_complete_medium': 10,
        'task_complete_high': 15,
        'task_complete_urgent': 20,
        'task_overdue': -10,
        'daily_streak_bonus': 25,
        'weekly_streak_bonus': 100,
        'consistency_bonus': 50,
        'streak_broken': -20,
    }
    
    @classmethod
    def get_or_create_user_level(cls, user):
        """Get or create user level object"""
        user_level, created = UserLevel.objects.get_or_create(
            user=user,
            defaults={
                'total_points': 0,
                'current_level': 1,
                'level_name': 'Beginner',
                'points_to_next_level': 100,
                'streak_days': 0,
                'longest_streak': 0,
                'last_activity_date': timezone.now().date()
            }
        )
        return user_level
    
    @classmethod
    def award_points(cls, user, points, transaction_type, description, task=None):
        """Award points to user and update level"""
        user_level = cls.get_or_create_user_level(user)
        
        # Create transaction record
        transaction = PointTransaction.objects.create(
            user=user,
            points=points,
            transaction_type=transaction_type,
            description=description,
            task=task
        )
        
        # Update user's total points
        user_level.total_points += points
        if user_level.total_points < 0:
            user_level.total_points = 0  # Don't allow negative total points
        
        # Update level
        user_level.update_level()
        
        logger.info(f"Awarded {points} points to {user.username} for {description}")
        return transaction
    
    @classmethod
    def handle_task_completion(cls, task):
        """Handle points when a task is completed"""
        user = task.user
        
        # Calculate points based on priority
        priority_points = {
            'low': cls.POINTS['task_complete_low'],
            'medium': cls.POINTS['task_complete_medium'],
            'high': cls.POINTS['task_complete_high'],
            'urgent': cls.POINTS['task_complete_urgent'],
        }
        
        points = priority_points.get(task.priority, cls.POINTS['task_complete_medium'])
        
        # Bonus for completing on time
        if task.due_date and timezone.now().date() <= task.due_date.date():
            points += 5  # On-time bonus
            description = f"Completed '{task.title}' on time ({task.get_priority_display()} priority)"
        else:
            description = f"Completed '{task.title}' ({task.get_priority_display()} priority)"
        
        # Award points
        cls.award_points(user, points, 'task_complete', description, task)
        
        # Update daily activity
        cls.update_daily_activity(user)
        
        # Check for streak bonuses
        cls.check_streak_bonuses(user)
        
        # Check for achievements
        cls.check_achievements(user)
    
    @classmethod
    def handle_task_overdue(cls, task):
        """Handle points when a task becomes overdue"""
        user = task.user
        points = cls.POINTS['task_overdue']
        description = f"Task '{task.title}' became overdue"
        
        cls.award_points(user, points, 'task_overdue', description, task)
        cls.update_daily_activity(user)
    
    @classmethod
    def update_daily_activity(cls, user):
        """Update daily activity tracking"""
        today = timezone.now().date()
        
        # Get today's tasks
        from tasks.models import Task
        today_tasks = Task.objects.filter(
            user=user,
            created_at__date=today
        )
        
        completed_tasks = today_tasks.filter(status='done').count()
        total_tasks = today_tasks.count()
        
        # Update or create daily activity
        daily_activity, created = DailyActivity.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'tasks_completed': completed_tasks,
                'tasks_total': total_tasks,
                'points_earned': 0
            }
        )
        
        if not created:
            daily_activity.tasks_completed = completed_tasks
            daily_activity.tasks_total = total_tasks
            daily_activity.save()
        
        return daily_activity
    
    @classmethod
    def check_streak_bonuses(cls, user):
        """Check and award streak bonuses"""
        user_level = cls.get_or_create_user_level(user)
        today = timezone.now().date()
        
        # Get recent daily activities
        recent_activities = DailyActivity.objects.filter(
            user=user,
            date__gte=today - timedelta(days=30)
        ).order_by('-date')
        
        # Calculate current streak
        current_streak = 0
        for activity in recent_activities:
            if activity.is_successful_day:
                current_streak += 1
            else:
                break
        
        # Update streak in user level
        old_streak = user_level.streak_days
        user_level.streak_days = current_streak
        user_level.last_activity_date = today
        
        if current_streak > user_level.longest_streak:
            user_level.longest_streak = current_streak
        
        # Award streak bonuses
        if current_streak > old_streak:
            # Daily streak bonus
            if current_streak >= 3:  # Minimum 3 days for bonus
                bonus_points = cls.POINTS['daily_streak_bonus']
                cls.award_points(
                    user, bonus_points, 'daily_streak',
                    f"Daily streak bonus: {current_streak} days!"
                )
            
            # Weekly streak bonus
            if current_streak % 7 == 0 and current_streak >= 7:
                bonus_points = cls.POINTS['weekly_streak_bonus']
                cls.award_points(
                    user, bonus_points, 'daily_streak',
                    f"Weekly streak bonus: {current_streak} days!"
                )
        
        # Penalty for breaking streak
        elif old_streak >= 3 and current_streak == 0:
            penalty_points = cls.POINTS['streak_broken']
            cls.award_points(
                user, penalty_points, 'streak_broken',
                f"Streak broken after {old_streak} days"
            )
        
        user_level.save()
    
    @classmethod
    def check_achievements(cls, user):
        """Check and award achievements"""
        user_level = cls.get_or_create_user_level(user)
        
        # Get all available achievements
        achievements = Achievement.objects.filter(is_active=True)
        
        for achievement in achievements:
            # Skip if user already has this achievement
            if UserAchievement.objects.filter(user=user, achievement=achievement).exists():
                continue
            
            # Check criteria
            earned = False
            
            if achievement.criteria_type == 'streak':
                earned = user_level.streak_days >= achievement.criteria_value
            elif achievement.criteria_type == 'level':
                earned = user_level.current_level >= achievement.criteria_value
            elif achievement.criteria_type == 'total_points':
                earned = user_level.total_points >= achievement.criteria_value
            elif achievement.criteria_type == 'tasks_completed':
                from tasks.models import Task
                completed_count = Task.objects.filter(user=user, status='done').count()
                earned = completed_count >= achievement.criteria_value
            
            if earned:
                # Award achievement
                UserAchievement.objects.create(user=user, achievement=achievement)
                
                # Award points
                if achievement.points_reward > 0:
                    cls.award_points(
                        user, achievement.points_reward, 'manual',
                        f"Achievement unlocked: {achievement.name}"
                    )
                
                logger.info(f"User {user.username} earned achievement: {achievement.name}")
    
    @classmethod
    def get_user_stats(cls, user):
        """Get comprehensive user stats"""
        user_level = cls.get_or_create_user_level(user)
        
        # Recent transactions
        recent_transactions = PointTransaction.objects.filter(user=user)[:10]
        
        # Recent daily activities
        recent_activities = DailyActivity.objects.filter(user=user)[:7]
        
        # User achievements
        user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement')
        
        return {
            'level': user_level,
            'recent_transactions': recent_transactions,
            'recent_activities': recent_activities,
            'achievements': user_achievements,
            'total_achievements': Achievement.objects.filter(is_active=True).count(),
        }
    
    @classmethod
    def create_default_achievements(cls):
        """Create default achievements"""
        default_achievements = [
            # Streak achievements
            {'name': 'Getting Started', 'description': 'Complete tasks for 3 consecutive days', 'icon': '🌱', 'points_reward': 50, 'criteria_type': 'streak', 'criteria_value': 3},
            {'name': 'Week Warrior', 'description': 'Complete tasks for 7 consecutive days', 'icon': '⚔️', 'points_reward': 100, 'criteria_type': 'streak', 'criteria_value': 7},
            {'name': 'Consistency King', 'description': 'Complete tasks for 30 consecutive days', 'icon': '👑', 'points_reward': 500, 'criteria_type': 'streak', 'criteria_value': 30},
            
            # Level achievements
            {'name': 'Level Up!', 'description': 'Reach Level 5', 'icon': '📈', 'points_reward': 200, 'criteria_type': 'level', 'criteria_value': 5},
            {'name': 'Expert Level', 'description': 'Reach Level 10', 'icon': '🎓', 'points_reward': 1000, 'criteria_type': 'level', 'criteria_value': 10},
            
            # Task completion achievements
            {'name': 'Task Master', 'description': 'Complete 50 tasks', 'icon': '✅', 'points_reward': 300, 'criteria_type': 'tasks_completed', 'criteria_value': 50},
            {'name': 'Productivity Pro', 'description': 'Complete 100 tasks', 'icon': '🚀', 'points_reward': 500, 'criteria_type': 'tasks_completed', 'criteria_value': 100},
            
            # Points achievements
            {'name': 'Point Collector', 'description': 'Earn 1000 total points', 'icon': '💎', 'points_reward': 0, 'criteria_type': 'total_points', 'criteria_value': 1000},
            {'name': 'Point Master', 'description': 'Earn 5000 total points', 'icon': '💯', 'points_reward': 0, 'criteria_type': 'total_points', 'criteria_value': 5000},
        ]
        
        for achievement_data in default_achievements:
            Achievement.objects.get_or_create(
                name=achievement_data['name'],
                defaults=achievement_data
            )
