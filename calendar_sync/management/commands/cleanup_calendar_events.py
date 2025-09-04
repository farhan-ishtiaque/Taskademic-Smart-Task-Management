from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from calendar_sync.models import TaskCalendarSync
from calendar_sync.services import GoogleCalendarService
from tasks.models import Task


class Command(BaseCommand):
    help = 'Clean up orphaned Google Calendar events for deleted tasks'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Clean up calendar events for specific user ID only'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion of calendar events even if task still exists'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        user_id = options['user_id']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get users to process
        if user_id:
            try:
                users = [User.objects.get(id=user_id)]
                self.stdout.write(f'Processing user ID: {user_id}')
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {user_id} not found')
                )
                return
        else:
            users = User.objects.filter(calendar_tokens__isnull=False).distinct()
            self.stdout.write(f'Processing {users.count()} users with calendar tokens')
        
        total_cleaned = 0
        
        for user in users:
            self.stdout.write(f'\n👤 Processing user: {user.username}')
            
            calendar_service = GoogleCalendarService(user)
            if not calendar_service.is_sync_enabled():
                self.stdout.write(f'  ⏭️  Calendar sync not enabled for {user.username}')
                continue
            
            # Find orphaned sync records (where task no longer exists)
            orphaned_syncs = TaskCalendarSync.objects.filter(
                task__user=user,
                sync_status__in=['synced', 'updated']
            ).exclude(
                task__in=Task.objects.filter(user=user)
            )
            
            self.stdout.write(f'  🔍 Found {orphaned_syncs.count()} orphaned sync records')
            
            for sync_record in orphaned_syncs:
                try:
                    if dry_run:
                        self.stdout.write(
                            f'    [DRY RUN] Would delete: Calendar {sync_record.calendar_id}, '
                            f'Event {sync_record.google_event_id}'
                        )
                    else:
                        # Create a temporary task object for the delete method
                        temp_task = Task(id=sync_record.task_id, user=user)
                        temp_task._state.adding = False  # Mark as existing object
                        
                        success = calendar_service.delete_event(temp_task)
                        if success:
                            self.stdout.write(
                                f'    ✅ Deleted calendar event: {sync_record.google_event_id}'
                            )
                            total_cleaned += 1
                        else:
                            self.stdout.write(
                                f'    ❌ Failed to delete calendar event: {sync_record.google_event_id}'
                            )
                
                except Exception as e:
                    self.stdout.write(
                        f'    ❌ Error processing sync record {sync_record.id}: {e}'
                    )
            
            # Also check for sync records where task still exists but user wants to force cleanup
            if force:
                all_syncs = TaskCalendarSync.objects.filter(
                    task__user=user,
                    sync_status__in=['synced', 'updated']
                )
                
                self.stdout.write(f'  🔧 Force mode: Processing {all_syncs.count()} sync records')
                
                for sync_record in all_syncs:
                    try:
                        if dry_run:
                            self.stdout.write(
                                f'    [DRY RUN] Would force delete: Calendar {sync_record.calendar_id}, '
                                f'Event {sync_record.google_event_id}'
                            )
                        else:
                            task = sync_record.task
                            success = calendar_service.delete_event(task)
                            if success:
                                self.stdout.write(
                                    f'    ✅ Force deleted calendar event for task: {task.title}'
                                )
                                total_cleaned += 1
                            else:
                                self.stdout.write(
                                    f'    ❌ Failed to force delete calendar event for task: {task.title}'
                                )
                    
                    except Exception as e:
                        self.stdout.write(
                            f'    ❌ Error force processing sync record {sync_record.id}: {e}'
                        )
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Cleanup completed! Processed {total_cleaned} calendar events')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'\n📊 Dry run completed! Found {total_cleaned} items that would be cleaned up')
            )
