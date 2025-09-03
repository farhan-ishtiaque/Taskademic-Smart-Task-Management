from django.db import models
from django.contrib.auth.models import User
from tasks.models import Task
import json


class GoogleCalendarSettings(models.Model):
    """User settings for Google Calendar sync"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='calendar_settings')
    sync_enabled = models.BooleanField(default=False)
    calendar_id = models.CharField(max_length=255, default='primary')
    last_sync = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Sync: {'Enabled' if self.sync_enabled else 'Disabled'}"

    class Meta:
        verbose_name = 'Google Calendar Settings'
        verbose_name_plural = 'Google Calendar Settings'


class GoogleCalendarToken(models.Model):
    """Store Google OAuth tokens for calendar access"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='calendar_token')
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expires_at = models.DateTimeField()
    scope = models.TextField(default='https://www.googleapis.com/auth/calendar')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Calendar Token"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() >= self.token_expires_at

    def get_token_dict(self):
        """Return token in the format expected by Google API client"""
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_at': self.token_expires_at.timestamp(),
            'scope': self.scope.split(' '),
            'token_type': 'Bearer'
        }

    class Meta:
        verbose_name = 'Google Calendar Token'
        verbose_name_plural = 'Google Calendar Tokens'


class TaskCalendarSync(models.Model):
    """Track sync status between tasks and Google Calendar events"""
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='calendar_sync')
    google_event_id = models.CharField(max_length=255)
    calendar_id = models.CharField(max_length=255, default='primary')
    last_synced = models.DateTimeField(auto_now=True)
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('synced', 'Synced'),
            ('pending', 'Pending'),
            ('error', 'Error'),
            ('deleted', 'Deleted')
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Task: {self.task.title} - Event: {self.google_event_id}"

    class Meta:
        verbose_name = 'Task Calendar Sync'
        verbose_name_plural = 'Task Calendar Syncs'
