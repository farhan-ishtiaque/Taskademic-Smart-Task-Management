from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    TECHNIQUE_CHOICES = [
        ('pomodoro', 'Pomodoro (25min work, 5min break)'),
        ('52_17', '52/17 Rule (52min work, 17min break)'),
        ('1_3_5', '1-3-5 Rule (1 big, 3 medium, 5 small tasks)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    preferred_technique = models.CharField(max_length=20, choices=TECHNIQUE_CHOICES, default='pomodoro')
    study_hours_per_day = models.IntegerField(default=4)
    timezone = models.CharField(max_length=50, default='UTC')
    streak_count = models.IntegerField(default=0)
    last_activity = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - Level {self.level}"
    
    def update_level(self):
        """Update user level based on points"""
        new_level = (self.total_points // 100) + 1
        if new_level != self.level:
            self.level = new_level
            self.save()
            return True
        return False
    
    def add_points(self, points):
        """Add points and update level"""
        self.total_points += points
        level_up = self.update_level()
        self.save()
        return level_up

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            preferred_technique='pomodoro',
            study_hours_per_day=4,
            timezone='UTC',
            total_points=0,
            level=1,
            streak_count=0
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
    else:
        UserProfile.objects.create(user=instance)
