from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import math


class UserLevel(models.Model):
    """User's current level and points"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='level')
    total_points = models.IntegerField(default=0)
    current_level = models.IntegerField(default=1)
    level_name = models.CharField(max_length=50, default='Beginner')
    points_to_next_level = models.IntegerField(default=100)
    streak_days = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def level_progress_percentage(self):
        """Calculate progress percentage to next level"""
        if self.points_to_next_level == 0:
            return 100
        current_level_base = self.get_level_base_points(self.current_level)
        next_level_base = self.get_level_base_points(self.current_level + 1)
        points_in_current_level = self.total_points - current_level_base
        points_needed_for_level = next_level_base - current_level_base
        
        if points_needed_for_level == 0:
            return 100
        return min(100, (points_in_current_level / points_needed_for_level) * 100)

    @staticmethod
    def get_level_base_points(level):
        """Calculate base points required for a level"""
        if level <= 1:
            return 0
        # Exponential growth: level 2=100, level 3=250, level 4=450, etc.
        return int(50 * (level ** 2) - 50 * level)

    @staticmethod
    def get_level_name(level):
        """Get level name based on level number"""
        level_names = {
            1: 'Beginner',
            2: 'Novice',
            3: 'Apprentice',
            4: 'Skilled',
            5: 'Expert',
            6: 'Advanced',
            7: 'Master',
            8: 'Grandmaster',
            9: 'Legend',
            10: 'Mythic'
        }
        if level > 10:
            return f'Mythic {level - 10}'
        return level_names.get(level, 'Beginner')

    def update_level(self):
        """Update user level based on total points"""
        new_level = 1
        while self.total_points >= self.get_level_base_points(new_level + 1):
            new_level += 1
        
        if new_level > self.current_level:
            # Level up!
            old_level = self.current_level
            self.current_level = new_level
            self.level_name = self.get_level_name(new_level)
            
            # Create level up achievement
            PointTransaction.objects.create(
                user=self.user,
                points=0,
                transaction_type='level_up',
                description=f'Level up from {old_level} to {new_level}!'
            )
        
        self.level_name = self.get_level_name(self.current_level)
        next_level_points = self.get_level_base_points(self.current_level + 1)
        self.points_to_next_level = next_level_points - self.total_points
        self.save()

    def __str__(self):
        return f"{self.user.username} - Level {self.current_level} ({self.total_points} points)"


class PointTransaction(models.Model):
    """Record of point transactions"""
    TRANSACTION_TYPES = [
        ('task_complete', 'Task Completed'),
        ('task_overdue', 'Task Overdue'),
        ('daily_streak', 'Daily Streak Bonus'),
        ('streak_broken', 'Streak Broken'),
        ('consistency_bonus', 'Consistency Bonus'),
        ('level_up', 'Level Up'),
        ('manual', 'Manual Adjustment'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_transactions')
    points = models.IntegerField()  # Can be positive or negative
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField()
    task = models.ForeignKey('tasks.Task', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.points >= 0 else ''
        return f"{self.user.username}: {sign}{self.points} points - {self.get_transaction_type_display()}"


class DailyActivity(models.Model):
    """Track daily task completion for streak calculation"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_activities')
    date = models.DateField()
    tasks_completed = models.IntegerField(default=0)
    tasks_total = models.IntegerField(default=0)
    points_earned = models.IntegerField(default=0)
    streak_day = models.IntegerField(default=0)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']

    @property
    def completion_rate(self):
        """Calculate completion rate as percentage"""
        if self.tasks_total == 0:
            return 0
        return (self.tasks_completed / self.tasks_total) * 100

    @property
    def is_successful_day(self):
        """A successful day is when 70% or more tasks are completed"""
        return self.completion_rate >= 70

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.tasks_completed}/{self.tasks_total})"


class Achievement(models.Model):
    """Achievement definitions"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='🏆')
    points_reward = models.IntegerField(default=0)
    criteria_type = models.CharField(max_length=50)  # streak, level, tasks_completed, etc.
    criteria_value = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.points_reward} points"


class UserAchievement(models.Model):
    """User's earned achievements"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'achievement']

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"
