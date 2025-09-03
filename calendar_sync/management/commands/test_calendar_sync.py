from django.core.management.base import BaseCommand
from calendar_sync.services import GoogleCalendarService
from tasks.models import Task
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Test Google Calendar sync functionality'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, help='Username to test sync for')
        parser.add_argument('--task-id', type=int, help='Specific task ID to sync')
        parser.add_argument('--action', type=str, choices=['create', 'update', 'delete'], default='create')

    def handle(self, *args, **options):
        username = options.get('user')
        task_id = options.get('task_id')
        action = options.get('action')

        if not username:
            self.stdout.write(self.style.ERROR('Please specify a username with --user'))
            return

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} not found'))
            return

        calendar_service = GoogleCalendarService(user)

        # Check if user has calendar sync enabled
        if not calendar_service.is_sync_enabled():
            self.stdout.write(self.style.WARNING(f'Calendar sync is not enabled for user {username}'))
            self.stdout.write('Please connect Google Calendar first at: /calendar-sync/settings/')
            return

        if task_id:
            try:
                task = Task.objects.get(id=task_id, user=user)
            except Task.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Task {task_id} not found for user {username}'))
                return

            self.stdout.write(f'Testing {action} action for task: {task.title}')

            if action == 'create':
                success = calendar_service.create_event(task)
            elif action == 'update':
                success = calendar_service.update_event(task)
            elif action == 'delete':
                success = calendar_service.delete_event(task)

            if success:
                self.stdout.write(self.style.SUCCESS(f'Successfully {action}d calendar event for task'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to {action} calendar event for task'))

        else:
            # Test with user's first task
            tasks = Task.objects.filter(user=user)[:1]
            if not tasks.exists():
                self.stdout.write(self.style.WARNING(f'No tasks found for user {username}'))
                return

            task = tasks.first()
            self.stdout.write(f'Testing calendar sync with task: {task.title}')

            success = calendar_service.create_event(task)
            if success:
                self.stdout.write(self.style.SUCCESS('Calendar sync test successful!'))
            else:
                self.stdout.write(self.style.ERROR('Calendar sync test failed!'))
