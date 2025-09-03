from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from tasks.models import Task
from .services import PointsService
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Task)
def handle_task_completion(sender, instance, created, **kwargs):
    """Handle points when task is completed or becomes overdue"""
    if not created:  # Only for updates, not new tasks
        # Check if task was just completed (status changed to 'done' or completed_at was set)
        if (instance.status == 'done' and not getattr(instance, '_was_done', False)) or \
           (instance.completed_at and not getattr(instance, '_was_completed_at', None)):
            PointsService.handle_task_completion(instance)
            logger.info(f"Points awarded for completing task: {instance.title}")


@receiver(pre_save, sender=Task)
def track_task_completion_status(sender, instance, **kwargs):
    """Track if task was previously completed"""
    if instance.pk:
        try:
            old_task = Task.objects.get(pk=instance.pk)
            instance._was_done = old_task.status == 'done'
            instance._was_completed_at = old_task.completed_at
        except Task.DoesNotExist:
            instance._was_done = False
            instance._was_completed_at = None
    else:
        instance._was_done = False
        instance._was_completed_at = None


# You can also create a management command to check for overdue tasks
# and deduct points for them
