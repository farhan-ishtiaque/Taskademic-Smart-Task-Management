from django.core.management.base import BaseCommand
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Fix broken notification action URLs'

    def handle(self, *args, **options):
        notifications = Notification.objects.filter(
            notification_type='team_invite',
            action_url__isnull=False
        )
        
        fixed_count = 0
        for notification in notifications:
            # Check if the action_url points to a team_invite_id instead of notification_id
            if '/accept-invite/' in notification.action_url:
                # Fix the URL to use the notification ID
                notification.action_url = f'/notifications/accept-invite/{notification.id}/'
                notification.save()
                fixed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Fixed notification {notification.id}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully fixed {fixed_count} notifications')
        )
