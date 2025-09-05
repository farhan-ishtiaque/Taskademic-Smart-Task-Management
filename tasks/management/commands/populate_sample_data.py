from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from tasks.models import Category, Task


class Command(BaseCommand):
    help = 'Populate the database with sample data for demonstration'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample categories
        categories_data = [
            {'name': 'Work', 'color': '#3B82F6'},
            {'name': 'Personal', 'color': '#10B981'},
            {'name': 'Study', 'color': '#F59E0B'},
            {'name': 'Health', 'color': '#EF4444'},
            {'name': 'Finance', 'color': '#8B5CF6'},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'color': cat_data['color']}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Get or create demo user (email-based)
        demo_email = 'demo@taskademic.com'
        demo_user, created = User.objects.get_or_create(
            email=demo_email,
            defaults={
                'username': demo_email,  # Use email as username
                'first_name': 'Demo',
                'last_name': 'User'
            }
        )
        if created:
            demo_user.set_password('demo123')
            demo_user.save()
            self.stdout.write('Created demo user with email-based authentication')
        
        # Create sample tasks
        sample_tasks = [
            {
                'title': 'Complete project proposal',
                'description': 'Finish the Q4 project proposal and submit to management',
                'category': categories[0],  # Work
                'priority': 'high',
                'status': 'in_progress',
                'due_date': timezone.now() + timedelta(days=3)
            },
            {
                'title': 'Review team code',
                'description': 'Review pull requests from the development team',
                'category': categories[0],  # Work
                'priority': 'medium',
                'status': 'todo',
                'due_date': timezone.now() + timedelta(days=1)
            },
            {
                'title': 'Buy groceries',
                'description': 'Get ingredients for this week\'s meal prep',
                'category': categories[1],  # Personal
                'priority': 'low',
                'status': 'todo',
                'due_date': timezone.now() + timedelta(days=2)
            },
            {
                'title': 'Study Django REST Framework',
                'description': 'Complete the DRF tutorial and build a sample API',
                'category': categories[2],  # Study
                'priority': 'medium',
                'status': 'in_progress',
                'due_date': timezone.now() + timedelta(days=7)
            },
            {
                'title': 'Gym workout',
                'description': 'Upper body strength training session',
                'category': categories[3],  # Health
                'priority': 'medium',
                'status': 'done',
                'due_date': timezone.now() - timedelta(days=1)
            },
            {
                'title': 'Update budget spreadsheet',
                'description': 'Add Q4 expenses and review financial goals',
                'category': categories[4],  # Finance
                'priority': 'high',
                'status': 'review',
                'due_date': timezone.now() + timedelta(days=5)
            },
            {
                'title': 'Plan vacation',
                'description': 'Research destinations and book flights for summer vacation',
                'category': categories[1],  # Personal
                'priority': 'low',
                'status': 'todo',
                'due_date': timezone.now() + timedelta(days=30)
            },
            {
                'title': 'Client presentation',
                'description': 'Prepare slides for the client demo on Friday',
                'category': categories[0],  # Work
                'priority': 'urgent',
                'status': 'todo',
                'due_date': timezone.now() + timedelta(days=2)
            },
            {
                'title': 'Learn TypeScript',
                'description': 'Complete online TypeScript course and practice with examples',
                'category': categories[2],  # Study
                'priority': 'medium',
                'status': 'in_progress',
                'due_date': timezone.now() + timedelta(days=14)
            },
            {
                'title': 'Dentist appointment',
                'description': 'Regular dental checkup and cleaning',
                'category': categories[3],  # Health
                'priority': 'medium',
                'status': 'todo',
                'due_date': timezone.now() + timedelta(days=10)
            }
        ]
        
        tasks_created = 0
        for task_data in sample_tasks:
            task, created = Task.objects.get_or_create(
                title=task_data['title'],
                user=demo_user,
                defaults=task_data
            )
            if created:
                tasks_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(categories)} categories and {tasks_created} tasks'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                '\nDemo credentials:\n'
                'Username: demo\n'
                'Password: demo123\n'
                '\nAdmin credentials:\n'
                'Username: admin\n'
                'Password: admin\n'
            )
        )
