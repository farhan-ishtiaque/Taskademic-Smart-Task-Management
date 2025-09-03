from django import forms
from .models import Task


class TaskForm(forms.ModelForm):
    """Form for creating and updating tasks"""
    
    PRIORITY_CHOICES = [
        ('must', 'Must Have'),
        ('should', 'Should Have'), 
        ('could', 'Could Have'),
        ('wont', 'Won\'t Have'),
    ]
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter task title...',
            'required': True
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input form-textarea',
            'placeholder': 'Describe your task in detail...',
            'rows': 4
        })
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'priority-option'
        })
    )
    
    due_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-input'
        })
    )
    
    estimated_duration = forms.IntegerField(
        required=False,
        initial=30,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'min': '1',
            'placeholder': '30'
        })
    )
    
    category = forms.ChoiceField(
        choices=Task.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-input'
        })
    )
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'due_date', 'estimated_duration', 'category']
        
    def clean_priority(self):
        priority = self.cleaned_data.get('priority')
        if not priority:
            raise forms.ValidationError('Please select a priority level.')
        return priority
        
    def clean_estimated_duration(self):
        duration = self.cleaned_data.get('estimated_duration')
        if duration and duration < 1:
            raise forms.ValidationError('Duration must be at least 1 minute.')
        return duration
