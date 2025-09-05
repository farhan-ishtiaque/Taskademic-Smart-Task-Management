from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from tasks.models import Task
from .models import Notification, NotificationPreferences


@receiver(pre_save, sender=Task)
def track_task_changes(sender, instance, **kwargs):
    """Track task status changes for team notifications"""
    if instance.pk:  # Task is being updated, not created
        try:
            old_task = Task.objects.get(pk=instance.pk)
            instance._old_status = old_task.status
            instance._old_assigned_to = old_task.assigned_to
        except Task.DoesNotExist:
            instance._old_status = None
            instance._old_assigned_to = None
    else:
        instance._old_status = None
        instance._old_assigned_to = None


@receiver(post_save, sender=Task)
def send_team_task_notifications(sender, instance, created, **kwargs):
    """Send notifications for team task updates"""
    if not instance.team:
        return  # Not a team task
    
    if created:
        # New team task created - notify team members
        team_members = instance.team.members.exclude(id=instance.user.id)
        for member in team_members:
            prefs, _ = NotificationPreferences.objects.get_or_create(
                user=member,
                defaults={'team_updates': False}
            )
            
            if prefs.team_updates:
                Notification.objects.create(
                    user=member,
                    notification_type='team_task_update',
                    title='New Team Task Created',
                    message=f'{instance.user.get_full_name() or instance.user.username} created a new task: "{instance.title}"',
                    action_url=f'/tasks/team/{instance.team.id}/kanban/',
                    action_text='View Team Board',
                    task_id=instance.id,
                    team_id=instance.team.id
                )
    else:
        # Task was updated
        notifications_sent = []
        
        # Check for status change
        if hasattr(instance, '_old_status') and instance._old_status != instance.status:
            team_members = instance.team.members.exclude(id=instance.user.id)
            for member in team_members:
                prefs, _ = NotificationPreferences.objects.get_or_create(
                    user=member,
                    defaults={'team_updates': False}
                )
                
                if prefs.team_updates:
                    status_display = dict(Task.STATUS_CHOICES).get(instance.status, instance.status)
                    Notification.objects.create(
                        user=member,
                        notification_type='team_task_update',
                        title='Team Task Status Updated',
                        message=f'Task "{instance.title}" was moved to {status_display}',
                        action_url=f'/tasks/team/{instance.team.id}/kanban/',
                        action_text='View Team Board',
                        task_id=instance.id,
                        team_id=instance.team.id
                    )
                    notifications_sent.append(member.id)
        
        # Check for assignment change
        if (hasattr(instance, '_old_assigned_to') and 
            instance._old_assigned_to != instance.assigned_to):
            
            # Notify the newly assigned user
            if instance.assigned_to and instance.assigned_to != instance.user:
                prefs, _ = NotificationPreferences.objects.get_or_create(
                    user=instance.assigned_to,
                    defaults={'team_updates': False}
                )
                
                if prefs.team_updates:
                    Notification.objects.create(
                        user=instance.assigned_to,
                        notification_type='task_assigned',
                        title='Team Task Assigned to You',
                        message=f'You have been assigned the task: "{instance.title}"',
                        action_url=f'/tasks/team/{instance.team.id}/kanban/',
                        action_text='View Task',
                        task_id=instance.id,
                        team_id=instance.team.id
                    )
            
            # Notify other team members (excluding the assigned user and task owner)
            exclude_ids = [instance.user.id]
            if instance.assigned_to:
                exclude_ids.append(instance.assigned_to.id)
            
            team_members = instance.team.members.exclude(id__in=exclude_ids)
            for member in team_members:
                if member.id not in notifications_sent:  # Avoid duplicate notifications
                    prefs, _ = NotificationPreferences.objects.get_or_create(
                        user=member,
                        defaults={'team_updates': False}
                    )
                    
                    if prefs.team_updates:
                        assigned_name = instance.assigned_to.get_full_name() or instance.assigned_to.username if instance.assigned_to else "Unassigned"
                        Notification.objects.create(
                            user=member,
                            notification_type='team_task_update',
                            title='Team Task Assignment Changed',
                            message=f'Task "{instance.title}" was assigned to {assigned_name}',
                            action_url=f'/tasks/team/{instance.team.id}/kanban/',
                            action_text='View Team Board',
                            task_id=instance.id,
                            team_id=instance.team.id
                        )


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create default notification preferences for new users"""
    if created:
        NotificationPreferences.objects.create(
            user=instance,
            task_due_reminders=True,
            weekly_summary=True,
            team_updates=False
        )
