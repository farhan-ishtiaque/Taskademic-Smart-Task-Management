from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Update user timezone to fix calendar sync issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the user to update',
        )
        parser.add_argument(
            '--timezone',
            type=str,
            default='America/Chicago',
            help='Timezone to set (default: America/Chicago)',
        )

    def handle(self, *args, **options):
        email = options['email']
        timezone = options['timezone']
        
        if not email:
            self.stdout.write(self.style.ERROR('Please provide an email address with --email'))
            return
            
        try:
            user = User.objects.get(email=email)
            profile = user.userprofile
            old_timezone = profile.timezone
            profile.timezone = timezone
            profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated timezone for {email} from "{old_timezone}" to "{timezone}"'
                )
            )
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error updating timezone: {e}'))
