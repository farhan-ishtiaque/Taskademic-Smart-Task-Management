from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# Import UserProfile to avoid circular import
def get_user_profile(user):
    from accounts.models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile


class Category(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories', default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('must', 'Must Have'),
        ('should', 'Should Have'), 
        ('could', 'Could Have'),
        ('wont', 'Won\'t Have'),
    ]
    
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('done', 'Done'),
    ]
    
    CATEGORY_CHOICES = [
        ('work', 'Work'),
        ('personal', 'Personal'),
        ('study', 'Study'),
        ('health', 'Health'),
        ('learning', 'Learning'),
        ('social', 'Social'),
        ('finance', 'Finance'),
        ('creative', 'Creative'),
        ('other', 'Other'),
    ]
    
    FOCUS_CATEGORY_CHOICES = [
        ('', 'Not in Focus List'),
        ('big', '🎯 Big Thing (1)'),
        ('medium', '📋 Medium Thing (3)'),
        ('small', '✅ Small Thing (5)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Team collaboration fields
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks', help_text="Team member assigned to this task")
    
    due_date = models.DateTimeField(null=True, blank=True)
    reminder_minutes = models.IntegerField(default=15, help_text="Minutes before due date to send reminder")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='should')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='todo')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='work')
    focus_category = models.CharField(max_length=10, choices=FOCUS_CATEGORY_CHOICES, default='', blank=True, help_text="Manually assign to 1-3-5 focus categories")
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")
    points_awarded = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_complete(self):
        self.status = 'done'
        self.completed_at = timezone.now()
        self.points_awarded = 10
        self.save()
        
        # Update user points
        profile = get_user_profile(self.user)
        profile.total_points += 10
        profile.save()
    
    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['done']:
            return timezone.now() > self.due_date
        return False
    
    @property
    def is_assigned(self):
        """Check if task is assigned to someone"""
        return self.assigned_to is not None
    
    @property
    def assignment_status(self):
        """Get assignment status for display"""
        if not self.assigned_to:
            return "Unassigned"
        elif self.assigned_to == self.user:
            return "Self-assigned"
        else:
            return f"Assigned to {self.assigned_to.username}"
    
    @property
    def tag_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    # Team collaboration methods
    def can_be_viewed_by(self, user):
        """Check if user can view this task"""
        # Task owner can always view
        if self.user == user:
            return True
        # Assigned user can view
        if self.assigned_to == user:
            return True
        # Team members can view team tasks
        if self.team and user in self.team.members.all():
            return True
        return False
    
    def can_be_edited_by(self, user):
        """Check if user can edit this task"""
        # Task owner can always edit
        if self.user == user:
            return True
        # Assigned user can edit their assigned tasks
        if self.assigned_to == user:
            return True
        # Team creator can edit team tasks
        if self.team and self.team.created_by == user:
            return True
        return False
    
    def can_change_status(self, user):
        """Check if user can change task status"""
        # Anyone who can edit can change status
        return self.can_be_edited_by(user)
    
    @property
    def assignee_display(self):
        """Display name for assigned user"""
        if self.assigned_to:
            return self.assigned_to.get_full_name() or self.assigned_to.username
        return "Unassigned"
    
    def get_moscow_priority(self):
        """
        Get MoSCoW priority using the new deterministic planner.
        This replaces the old priority calculation methods.
        """
        from priority_analyzer.services import MoSCoWPriorityPlanner
        
        planner = MoSCoWPriorityPlanner()
        
        # Create task data for analysis
        tasks_data = {
            'now': timezone.now().isoformat(),
            'timezone': 'UTC',
            'tasks': [{
                'id': str(self.id),
                'title': self.title,
                'description': self.description or '',
                'due_at': self.due_date.isoformat() if self.due_date else None,
                'estimated_size': getattr(self, 'estimated_size', None),
                'course_weight': getattr(self, 'course_weight', None)
            }]
        }
        
        result = planner.analyze_tasks(tasks_data)
        
        # Find this task in the results
        for category, tasks in result['buckets'].items():
            for task in tasks:
                if task['id'] == str(self.id):
                    return category
        
        # Fallback to 'should' if not found
        return 'should'
    
    def get_moscow_details(self):
        """
        Get detailed MoSCoW analysis including score and reasoning.
        """
        from priority_analyzer.services import MoSCoWPriorityPlanner
        
        planner = MoSCoWPriorityPlanner()
        
        # Create task data for analysis
        tasks_data = {
            'now': timezone.now().isoformat(),
            'timezone': 'UTC',
            'tasks': [{
                'id': str(self.id),
                'title': self.title,
                'description': self.description or '',
                'due_at': self.due_date.isoformat() if self.due_date else None,
                'estimated_size': getattr(self, 'estimated_size', None),
                'course_weight': getattr(self, 'course_weight', None)
            }]
        }
        
        result = planner.analyze_tasks(tasks_data)
        
        # Find this task in the decision log
        for log_entry in result['decision_log']:
            if log_entry['id'] == str(self.id):
                return {
                    'category': log_entry['final'],
                    'score': log_entry['score'],
                    'task_type': log_entry['type'],
                    'importance': log_entry['importance'],
                    'urgency': log_entry['urgency'],
                    'due_in_days': log_entry['due_in_days'],
                    'reasoning': log_entry['matched_rule']
                }
        
        # Fallback
        return {
            'category': 'should',
            'score': 30,
            'task_type': 'Regular coursework',
            'importance': 3,
            'urgency': 0,
            'due_in_days': None,
            'reasoning': 'Default classification'
        }


class TimeBlock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_blocks')
    day_of_week = models.IntegerField()  # 0=Monday, 6=Sunday
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'day_of_week', 'start_time']
    
    def duration_minutes(self):
        """Calculate duration in minutes"""
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        return end_minutes - start_minutes
    
    def __str__(self):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return f"{self.user.username} - {days[self.day_of_week]} {self.start_time}-{self.end_time}"


class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"


class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task_attachments/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.filename} - {self.task.title}"
