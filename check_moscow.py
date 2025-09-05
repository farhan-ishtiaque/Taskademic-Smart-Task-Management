import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

from tasks.models import Task
from django.contrib.auth.models import User

user = User.objects.first()
if user:
    print(f'User: {user.username}')
    tasks = Task.objects.filter(user=user)
    print(f'Total tasks: {tasks.count()}')
    
    moscow_counts = {}
    for task in tasks:
        moscow = task.moscow_priority
        moscow_counts[moscow] = moscow_counts.get(moscow, 0) + 1
        print(f'- {task.title}: moscow_priority={moscow}')
    
    print(f'\nMoSCoW Distribution: {moscow_counts}')
else:
    print('No user found')
