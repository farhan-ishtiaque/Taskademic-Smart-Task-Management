from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tasks.models import Task
from points.services import PointsService
from points.models import UserLevel


class Command(BaseCommand):
    help = 'Test the points system by creating sample tasks and completing them'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username to test with', default='testuser')

    def handle(self, *args, **options):
        print("Starting points test...")
        username = options['username']
        print(f"Looking for user: {username}")
        
        try:
            user = User.objects.get(username=username)
            print(f"Found existing user: {user.username}")
        except User.DoesNotExist:
            # Create the user if it doesn't exist
            user = User.objects.create_user(
                username=username,
                email=f'{username}@example.com',
                password='testpass123'
            )
            print(f"Created new user: {user.username}")
            self.stdout.write(f'Created user: {username}')
        
        self.stdout.write(f'Testing points system for user: {user.username}')
        
        # Get initial points
        user_level = PointsService.get_or_create_user_level(user)
        initial_points = user_level.total_points
        self.stdout.write(f'Initial points: {initial_points}')
        
        # Create a test task
        task = Task.objects.create(
            user=user,
            title='Test Task for Points',
            description='This is a test task to verify the points system',
            priority='medium',
            status='in_progress'
        )
        self.stdout.write(f'Created test task: {task.title}')
        
        # Complete the task
        task.completed = True
        task.save()
        self.stdout.write('Marked task as completed')
        
        # Check points after completion
        user_level.refresh_from_db()
        final_points = user_level.total_points
        points_earned = final_points - initial_points
        
        self.stdout.write(f'Final points: {final_points}')
        self.stdout.write(f'Points earned: {points_earned}')
        self.stdout.write(f'Current level: {user_level.current_level} ({user_level.level_name})')
        self.stdout.write(f'Current streak: {user_level.streak_days} days')
        
        # Show recent transactions
        from points.models import PointTransaction
        recent_transactions = PointTransaction.objects.filter(user=user).order_by('-created_at')[:5]
        
        self.stdout.write('\nRecent transactions:')
        for transaction in recent_transactions:
            sign = '+' if transaction.points > 0 else ''
            self.stdout.write(f'  {sign}{transaction.points} pts - {transaction.description}')
        
        self.stdout.write(
            self.style.SUCCESS('Points system test completed successfully!')
        )
