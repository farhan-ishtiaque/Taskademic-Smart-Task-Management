from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Create a test notification for the current user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to create notification for')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
            
            # Create a test notification
            notification = Notification.objects.create(
                user=user,
                notification_type='team_invite',
                title='Test Notification',
                message='This is a test notification to verify the system is working.',
                action_text='Test Action'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created test notification for user "{username}"')
            )
            self.stdout.write(f'Notification ID: {notification.id}')
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" does not exist')
            )
