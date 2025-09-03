from django.core.management.base import BaseCommand
from points.services import PointsService


class Command(BaseCommand):
    help = 'Create default achievements for the points system'

    def handle(self, *args, **options):
        self.stdout.write('Creating default achievements...')
        
        PointsService.create_default_achievements()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created default achievements!')
        )
