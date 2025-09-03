from django.core.management.base import BaseCommand
from calendar_sync.models import GoogleCalendarSettings, GoogleCalendarToken, TaskCalendarSync
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Test calendar sync database tables'

    def handle(self, *args, **options):
        try:
            # Test table access
            settings_count = GoogleCalendarSettings.objects.count()
            token_count = GoogleCalendarToken.objects.count()
            sync_count = TaskCalendarSync.objects.count()
            
            self.stdout.write(self.style.SUCCESS(f'✅ GoogleCalendarSettings table: {settings_count} records'))
            self.stdout.write(self.style.SUCCESS(f'✅ GoogleCalendarToken table: {token_count} records'))
            self.stdout.write(self.style.SUCCESS(f'✅ TaskCalendarSync table: {sync_count} records'))
            
            # Test user access
            users = User.objects.count()
            self.stdout.write(self.style.SUCCESS(f'✅ Users in database: {users}'))
            
            self.stdout.write(self.style.SUCCESS('🎉 All calendar sync tables are working correctly!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error accessing tables: {e}'))
