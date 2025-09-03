from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from tasks.models import Task
from .services import GoogleCalendarService
from .models import TaskCalendarSync
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Task)
def sync_task_on_save(sender, instance, created, **kwargs):
    """Automatically sync task to Google Calendar when saved"""
    try:
        calendar_service = GoogleCalendarService(instance.user)
        
        if not calendar_service.is_sync_enabled():
            return
        
        if created:
            # New task - create calendar event
            calendar_service.create_event(instance)
            logger.info(f"Created calendar event for new task: {instance.title}")
        else:
            # Existing task - update calendar event
            calendar_service.update_event(instance)
            logger.info(f"Updated calendar event for task: {instance.title}")
            
    except Exception as e:
        logger.error(f"Error syncing task {instance.id} to calendar: {e}")


@receiver(post_delete, sender=Task)
def sync_task_on_delete(sender, instance, **kwargs):
    """Automatically delete calendar event when task is deleted"""
    try:
        calendar_service = GoogleCalendarService(instance.user)
        
        if not calendar_service.is_sync_enabled():
            return
        
        calendar_service.delete_event(instance)
        logger.info(f"Deleted calendar event for task: {instance.title}")
        
    except Exception as e:
        logger.error(f"Error deleting calendar event for task {instance.id}: {e}")


@receiver(pre_save, sender=Task)
def handle_task_completion(sender, instance, **kwargs):
    """Handle task completion status changes"""
    if instance.pk:  # Only for existing tasks
        try:
            old_task = Task.objects.get(pk=instance.pk)
            
            # Check if status changed to completed
            if old_task.status != 'completed' and instance.status == 'completed':
                calendar_service = GoogleCalendarService(instance.user)
                
                if calendar_service.is_sync_enabled():
                    # Update the calendar event to reflect completion
                    calendar_service.update_event(instance)
                    logger.info(f"Updated calendar event for completed task: {instance.title}")
                    
        except Task.DoesNotExist:
            pass  # New task, will be handled by post_save
        except Exception as e:
            logger.error(f"Error handling task completion for task {instance.id}: {e}")
