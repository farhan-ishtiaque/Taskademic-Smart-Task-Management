from django import forms
from django.contrib.auth.models import User
from .models import Task
from teams.models import Team
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
    
    # Team selection field - simple dropdown
    team = forms.ModelChoiceField(
        queryset=Team.objects.none(),
        required=False,
        empty_label="Personal Task",
        widget=forms.Select(attrs={
            'class': 'form-input'
        }),
        help_text="Optional: Select a team to share this task"
    )
    
    # Task assignment field
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label="Assign to team member (optional)",
        widget=forms.Select(attrs={
            'class': 'form-input'
        }),
        help_text="Assign this task to a team member"
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
        fields = ['title', 'description', 'team', 'assigned_to', 'priority', 'due_date', 'estimated_duration', 'category']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show teams where user is a member
        if user:
            self.fields['team'].queryset = user.teams.all()
            
            # Check if there's data being submitted
            if self.data:
                team_id = self.data.get('team')
                if team_id:
                    try:
                        from teams.models import Team
                        team = Team.objects.get(id=team_id)
                        self.fields['assigned_to'].queryset = team.members.all()
                    except (Team.DoesNotExist, ValueError):
                        self.fields['assigned_to'].queryset = User.objects.none()
                else:
                    self.fields['assigned_to'].queryset = User.objects.none()
            elif self.instance and self.instance.pk and self.instance.team:
                # If editing existing task with team, show team members
                self.fields['assigned_to'].queryset = self.instance.team.members.all()
            else:
                # For new tasks, initially empty (will be populated via JavaScript)
                self.fields['assigned_to'].queryset = User.objects.none()
        else:
            self.fields['team'].queryset = Team.objects.none()
            self.fields['assigned_to'].queryset = User.objects.none()
    
    def clean(self):
        """Custom form validation to handle dynamic assignment"""
        cleaned_data = super().clean()
        team = cleaned_data.get('team')
        assigned_to_id = self.data.get('assigned_to')
        
        # If team and assigned_to are provided
        if team and assigned_to_id:
            try:
                assigned_user = User.objects.get(id=assigned_to_id)
                # Check if user is in the team
                if assigned_user in team.members.all():
                    cleaned_data['assigned_to'] = assigned_user
                else:
                    self.add_error('assigned_to', 'Selected user is not a member of the chosen team.')
            except User.DoesNotExist:
                self.add_error('assigned_to', 'Selected user does not exist.')
        elif assigned_to_id and not team:
            self.add_error('assigned_to', 'Please select a team first before assigning.')
        
        return cleaned_data
    
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
