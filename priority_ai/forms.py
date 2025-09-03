from django import forms
from .priority_predictor import PriorityPredictor

class AIPriorityMixin:
    """
    Mixin to add AI priority prediction to task forms.
    """
    def clean(self):
        cleaned_data = super().clean()
        
        # Only predict if priority wasn't manually set
        if 'priority' not in cleaned_data or not cleaned_data['priority']:
            task_name = cleaned_data.get('name', '')
            task_description = cleaned_data.get('description', '')
            
            predictor = PriorityPredictor()
            priority, confidence = predictor.predict_priority(task_name, task_description)
            
            # Only use AI prediction if confidence is high enough
            if confidence >= 0.7:
                cleaned_data['priority'] = priority
            else:
                # Default to 'should' if confidence is low
                cleaned_data['priority'] = 'should'
        
        return cleaned_data
