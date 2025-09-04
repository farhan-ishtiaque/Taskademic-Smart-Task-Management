from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from tasks.models import Task
from notifications.models import Notification, NotificationPreferences


class Command(BaseCommand):
    help = 'Send due date reminder notifications'

    def handle(self, *args, **options):
        now = timezone.now()
        tomorrow = now + timedelta(days=1)
        
        # Get tasks due within the next 24 hours
        due_soon_tasks = Task.objects.filter(
            due_date__gte=now,
            due_date__lte=tomorrow,
            status__in=['todo', 'in_progress']
        ).select_related('user', 'assigned_to')
        
        notifications_created = 0
        
        for task in due_soon_tasks:
            # Check if we should notify the task owner
            if task.user:
                prefs, created = NotificationPreferences.objects.get_or_create(
                    user=task.user,
                    defaults={'task_due_reminders': True}
                )
                
                if prefs.task_due_reminders:
                    # Check if notification already exists for this task
                    existing = Notification.objects.filter(
                        user=task.user,
                        notification_type='task_due_reminder',
                        task_id=task.id,
                        created_at__date=now.date()
                    ).exists()
                    
                    if not existing:
                        Notification.objects.create(
                            user=task.user,
                            notification_type='task_due_reminder',
                            title='Task Due Soon',
                            message=f'Your task "{task.title}" is due on {task.due_date.strftime("%b %d, %Y at %I:%M %p")}',
                            action_url=f'/tasks/{task.id}/',
                            action_text='View Task',
                            task_id=task.id
                        )
                        notifications_created += 1
            
            # Check if we should notify the assigned user (if different from owner)
            if task.assigned_to and task.assigned_to != task.user:
                prefs, created = NotificationPreferences.objects.get_or_create(
                    user=task.assigned_to,
                    defaults={'task_due_reminders': True}
                )
                
                if prefs.task_due_reminders:
                    existing = Notification.objects.filter(
                        user=task.assigned_to,
                        notification_type='task_due_reminder',
                        task_id=task.id,
                        created_at__date=now.date()
                    ).exists()
                    
                    if not existing:
                        Notification.objects.create(
                            user=task.assigned_to,
                            notification_type='task_due_reminder',
                            title='Assigned Task Due Soon',
                            message=f'Your assigned task "{task.title}" is due on {task.due_date.strftime("%b %d, %Y at %I:%M %p")}',
                            action_url=f'/tasks/{task.id}/',
                            action_text='View Task',
                            task_id=task.id
                        )
                        notifications_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {notifications_created} due date reminder notifications')
        )
