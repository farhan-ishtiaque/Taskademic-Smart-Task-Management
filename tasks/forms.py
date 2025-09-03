from django import forms
from .models import Task
from priority_analyzer.services import DeepSeekPriorityAnalyzer

class TaskForm(forms.ModelForm):
    """Form for creating and updating tasks with AI priority prediction"""
    
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
    
    # Priority is hidden as it's determined automatically by DeepSeek API
    priority = forms.CharField(
        widget=forms.HiddenInput(),
        required=False  # Will be set automatically by the AI
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
    
    def save(self, commit=True):
        """Override save to ensure priority is set by DeepSeek API"""
        instance = super().save(commit=False)
        
        # Get priority from DeepSeek API
        analyzer = DeepSeekPriorityAnalyzer()
        priority = analyzer.analyze_priority(
            self.cleaned_data['title'],
            self.cleaned_data.get('description', '')
        )
        
        # Set the priority
        instance.priority = priority
        
        if commit:
            instance.save()
        return instance
        
    def clean_estimated_duration(self):
        duration = self.cleaned_data.get('estimated_duration')
        if duration and duration < 1:
            raise forms.ValidationError('Duration must be at least 1 minute.')
        return duration
