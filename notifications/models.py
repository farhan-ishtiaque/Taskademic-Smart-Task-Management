from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class NotificationPreferences(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    task_due_reminders = models.BooleanField(default=True)
    weekly_summary = models.BooleanField(default=True)
    team_updates = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} notification preferences"


class Notification(models.Model):
    """In-app notifications for users"""
    NOTIFICATION_TYPES = [
        ('team_invite', 'Team Invitation'),
        ('task_assigned', 'Task Assigned'),
        ('task_status_change', 'Task Status Changed'),
        ('team_join', 'Team Member Joined'),
        ('task_due_reminder', 'Task Due Reminder'),
        ('team_task_update', 'Team Task Update'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional links
    action_url = models.URLField(blank=True, null=True)
    action_text = models.CharField(max_length=50, blank=True, null=True)
    
    # Related objects (optional)
    team_invite_id = models.UUIDField(blank=True, null=True)
    team_id = models.UUIDField(blank=True, null=True)
    task_id = models.UUIDField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()
