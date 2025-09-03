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
    ]
    
    FOCUS_CATEGORY_CHOICES = [
        ('', 'Not in Focus List'),
        ('big', '🎯 Big Thing (1)'),
        ('medium', '📋 Medium Thing (3)'),
        ('small', '✅ Small Thing (5)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.IntegerField(default=60, help_text="Duration in minutes")
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
    def tag_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def calculate_priority_score(self):
        """
        Calculate priority score using the formula:
        priority_score = (importance_weight × α) + (β ÷ max(days_left, 1)) + γ
        
        Where:
        - α = 10 (importance scaling factor)
        - β = 40 (urgency scaling factor, set to beat lower priority tasks)
        - γ = 0 (additional factors, not used currently)
        """
        from datetime import datetime
        
        # MoSCoW importance weights
        importance_weights = {
            'must': 40,    # Must Have
            'should': 30,  # Should Have  
            'could': 20,   # Could Have
            'wont': 10     # Won't Have
        }
        
        # Constants for the formula
        alpha = 10  # Importance scaling factor
        beta = 40   # Urgency scaling factor
        gamma = 0   # Additional factors (not used)
        
        # Get importance weight
        importance_weight = importance_weights.get(self.priority, 20)
        
        # Calculate days left until deadline
        if self.due_date:
            days_left = (self.due_date.date() - timezone.now().date()).days
            # Ensure minimum of 1 day for the formula
            days_left = max(days_left, 1)
        else:
            # If no deadline, assume far future (low urgency)
            days_left = 365
        
        # Apply the priority formula
        priority_score = (importance_weight * alpha) + (beta / days_left) + gamma
        
        return round(priority_score, 2)
    
    def get_auto_priority(self):
        """
        Automatically determine MoSCoW priority based on score and deadline.
        This method considers both the selected MoSCoW option and deadline urgency.
        """
        score = self.calculate_priority_score()
        
        # If task is due soon (within 1-2 days), escalate priority
        if self.due_date:
            days_left = (self.due_date.date() - timezone.now().date()).days
            
            # Tasks due tomorrow or today get boosted
            if days_left <= 1:
                if self.priority in ['should', 'could']:
                    return 'must'  # Escalate to Must Have
                elif self.priority == 'wont':
                    return 'should'  # Escalate Won't to Should
            
            # Tasks due within 3 days get moderate boost
            elif days_left <= 3:
                if self.priority == 'could':
                    return 'should'  # Escalate Could to Should
                elif self.priority == 'wont':
                    return 'could'  # Escalate Won't to Could
        
        # Return original priority if no escalation needed
        return self.priority


class TimeBlock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_blocks')
    day_of_week = models.IntegerField()  # 0=Monday, 6=Sunday
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'day_of_week', 'start_time']
    
    def __str__(self):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return f"{self.user.username} - {days[self.day_of_week]} {self.start_time}-{self.end_time}"
        self.status = 'done'
        self.save()
    
    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['done', 'cancelled']:
            return timezone.now() > self.due_date
        return False
    
    @property
    def tag_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def get_time_spent(self):
        """Calculate time spent on task"""
        if self.actual_hours:
            return self.actual_hours
        return 0
    
    def get_time_remaining(self):
        """Calculate estimated time remaining"""
        if self.estimated_hours and self.actual_hours:
            return max(0, self.estimated_hours - self.actual_hours)
        elif self.estimated_hours:
            return self.estimated_hours
        return 0


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
