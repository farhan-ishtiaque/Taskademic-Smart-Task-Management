from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.models import Notification

User = get_user_model()

class Command(BaseCommand):
    help = 'Send a test notification to verify the mark as read functionality'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username to send notification to', default='farhan')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
            
            # Create a test notification
            notification = Notification.objects.create(
                user=user,
                title='Test Notification',
                message='This is a test notification to verify the mark as read functionality works correctly.',
                notification_type='general',
                is_read=False
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created test notification for user {username} (ID: {notification.id})'
                )
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} not found')
            )
