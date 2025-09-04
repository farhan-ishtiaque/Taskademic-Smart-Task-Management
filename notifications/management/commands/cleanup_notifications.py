from django.core.management.base import BaseCommand
from django.db.models import Count
from notifications.models import Notification
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Clean up duplicate and old notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete notifications older than this many days (default: 30)'
        )
        parser.add_argument(
            '--remove-duplicates',
            action='store_true',
            help='Remove duplicate notifications'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Remove old notifications
        old_notifications = Notification.objects.filter(
            created_at__lt=cutoff_date,
            is_read=True
        )
        old_count = old_notifications.count()
        old_notifications.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Deleted {old_count} old notifications (older than {days} days)')
        )
        
        # Remove duplicate team invites if requested
        if options['remove_duplicates']:
            # Find duplicate team invitations for the same user/team combination
            duplicates_removed = 0
            
            # Group by user, team_id, and notification_type
            duplicate_groups = Notification.objects.filter(
                notification_type='team_invite'
            ).values(
                'user_id', 'team_id', 'notification_type'
            ).annotate(
                count=Count('id')
            ).filter(count__gt=1)
            
            for group in duplicate_groups:
                # Keep the most recent notification, delete the rest
                notifications = Notification.objects.filter(
                    user_id=group['user_id'],
                    team_id=group['team_id'],
                    notification_type=group['notification_type']
                ).order_by('-created_at')
                
                # Delete all but the first (most recent)
                to_delete = notifications[1:]
                count = len(to_delete)
                for notif in to_delete:
                    notif.delete()
                duplicates_removed += count
            
            self.stdout.write(
                self.style.SUCCESS(f'Removed {duplicates_removed} duplicate notifications')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Notification cleanup completed successfully')
        )
