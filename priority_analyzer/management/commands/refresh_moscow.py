from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.cache import cache
from priority_analyzer.signals import MoSCoWCacheService


class Command(BaseCommand):
    help = 'Refresh MoSCoW matrix for all users - run daily to handle date changes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Refresh MoSCoW matrix for specific user ID only'
        )
        parser.add_argument(
            '--clear-all',
            action='store_true',
            help='Clear all MoSCoW cache entries'
        )
    
    def handle(self, *args, **options):
        if options['clear_all']:
            # Clear all MoSCoW related cache entries
            self.stdout.write('Clearing all MoSCoW cache entries...')
            cache_keys = cache.keys('moscow_matrix_*')
            if cache_keys:
                cache.delete_many(cache_keys)
                self.stdout.write(
                    self.style.SUCCESS(f'Cleared {len(cache_keys)} cache entries')
                )
            else:
                self.stdout.write('No cache entries found to clear')
            return
        
        if options['user_id']:
            # Refresh for specific user
            try:
                user = User.objects.get(id=options['user_id'])
                self.stdout.write(f'Refreshing MoSCoW matrix for user: {user.username}')
                result = MoSCoWCacheService.force_refresh_moscow_analysis(user)
                
                # Count tasks in each bucket
                counts = {bucket: len(tasks) for bucket, tasks in result['buckets'].items()}
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Refreshed MoSCoW matrix for {user.username}: '
                        f'Must: {counts["must"]}, Should: {counts["should"]}, '
                        f'Could: {counts["could"]}, Won\'t: {counts["wont"]}'
                    )
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {options["user_id"]} not found')
                )
        else:
            # Refresh for all users with active tasks
            self.stdout.write('Refreshing MoSCoW matrix for all users with active tasks...')
            
            users_with_tasks = User.objects.filter(
                owned_tasks__status__in=['todo', 'in_progress']
            ).distinct()
            
            total_users = users_with_tasks.count()
            self.stdout.write(f'Found {total_users} users with active tasks')
            
            refreshed_count = 0
            for user in users_with_tasks:
                try:
                    result = MoSCoWCacheService.force_refresh_moscow_analysis(user)
                    refreshed_count += 1
                    
                    # Count tasks in each bucket
                    counts = {bucket: len(tasks) for bucket, tasks in result['buckets'].items()}
                    self.stdout.write(
                        f'  {user.username}: Must: {counts["must"]}, '
                        f'Should: {counts["should"]}, Could: {counts["could"]}, '
                        f'Won\'t: {counts["wont"]}'
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Failed to refresh MoSCoW matrix for {user.username}: {str(e)}'
                        )
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully refreshed MoSCoW matrix for {refreshed_count}/{total_users} users'
                )
            )
