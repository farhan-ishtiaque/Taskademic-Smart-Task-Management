from django import forms
import requests
from django.conf import settings

class AIPriorityMixin:
    """Mixin to add AI-powered priority prediction to forms"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['data-priority-analyze'] = 'true'
        self.fields['description'].widget.attrs['data-priority-analyze'] = 'true'
        
    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        description = cleaned_data.get('description', '')
        
        # If this is a new task (no instance) or priority wasn't set
        if not self.instance.pk or not cleaned_data.get('priority'):
            try:
                # Call our priority analyzer API
                response = requests.post(
                    'http://localhost:8000/priority/analyze/',
                    json={
                        'task_name': title,
                        'task_description': description
                    }
                )
                
                if response.status_code == 200:
                    priority = response.json().get('priority')
                    if priority in dict(self.fields['priority'].choices).keys():
                        cleaned_data['priority'] = priority
                
            except Exception as e:
                # Log the error but don't block form submission
                print(f"Priority analysis error: {e}")
        
        return cleaned_data
