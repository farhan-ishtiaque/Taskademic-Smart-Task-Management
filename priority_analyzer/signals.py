from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from tasks.models import Task
from .services import MoSCoWPriorityPlanner


def clear_moscow_cache(user_id):
    """Clear MoSCoW matrix cache for a specific user"""
    cache_key = f'moscow_matrix_{user_id}'
    cache.delete(cache_key)


@receiver(post_save, sender=Task)
def task_saved_handler(sender, instance, created, **kwargs):
    """
    Signal handler for when a task is created or updated.
    Triggers MoSCoW matrix rebuild for the task owner.
    """
    # Clear cache to trigger recalculation
    clear_moscow_cache(instance.user.id)
    
    # If task has assigned_to user, also clear their cache
    if instance.assigned_to and instance.assigned_to != instance.user:
        clear_moscow_cache(instance.assigned_to.id)


@receiver(post_delete, sender=Task)
def task_deleted_handler(sender, instance, **kwargs):
    """
    Signal handler for when a task is deleted.
    Triggers MoSCoW matrix rebuild for the task owner.
    """
    # Clear cache to trigger recalculation
    clear_moscow_cache(instance.user.id)
    
    # If task had assigned_to user, also clear their cache
    if instance.assigned_to and instance.assigned_to != instance.user:
        clear_moscow_cache(instance.assigned_to.id)


class MoSCoWCacheService:
    """Service for managing cached MoSCoW analysis results"""
    
    @staticmethod
    def get_moscow_analysis(user, force_refresh=False):
        """
        Get cached MoSCoW analysis for a user, or calculate if not cached.
        """
        cache_key = f'moscow_matrix_{user.id}'
        
        if not force_refresh:
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
        
        # Get user's active tasks
        tasks = Task.objects.filter(
            user=user,
            status__in=['todo', 'in_progress']
        )
        
        # Calculate MoSCoW analysis
        planner = MoSCoWPriorityPlanner()
        result = planner.analyze_django_tasks(tasks, user_timezone='UTC')
        
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, result, 3600)
        
        return result
    
    @staticmethod
    def force_refresh_moscow_analysis(user):
        """Force refresh of MoSCoW analysis for a user"""
        return MoSCoWCacheService.get_moscow_analysis(user, force_refresh=True)
