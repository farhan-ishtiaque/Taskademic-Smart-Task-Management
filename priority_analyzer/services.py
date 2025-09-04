import json
import math
from datetime import datetime, timezone as dt_timezone
from django.utils import timezone
from django.conf import settings


class MoSCoWPriorityPlanner:
    """
    Deterministic planner for student workloads using MoSCoW buckets.
    Classifies tasks using explicit rules that combine task type (importance) and deadline (urgency).
    Output is idempotent: same input produces same output every time.
    """
    
    def __init__(self):
        # Deterministic keyword mapping for task types (ordered by priority)
        self.task_type_keywords = {
            'Major academic': [
                'research paper', 'term paper', 'thesis', 'dissertation', 'capstone',
                'senior project', 'major presentation', 'defense', 'project', 
                'midterm', 'final', 'major exam'
            ],
            'Regular coursework': [
                'homework', 'assignment', 'lab report', 'problem set', 'pset',
                'quiz', 'weekly quiz', 'chapter exercises', 'discussion post',
                'forum participation', 'presentation', 'class presentation'
            ],
            'Supplementary': [
                'learn', 'study', 'practice', 'review notes', 'study notes',
                'flashcards', 'extra credit', 'bonus assignment',
                'supplementary reading', 'optional exercises'
            ],
            'Non-academic': [
                'cooking', 'shopping', 'laundry', 'clean room', 'entertainment',
                'game', 'movie', 'hobby', 'gym', 'doctor', 'appointment', 
                'medical', 'dentist', 'checkup', 'personal', 'errands',
                'grocery', 'bank', 'pharmacy', 'hospital', 'clinic', 'health'
            ]
        }
        
        # Base importance weights by type
        self.importance_weights = {
            'Major academic': 4,
            'Regular coursework': 3,
            'Supplementary': 2,
            'Non-academic': 1
        }
    
    def classify_task_type(self, title, description=""):
        """
        Deterministically classify task into one type using first matching keyword.
        Returns task type based on ordered keyword matching.
        """
        text = f"{title} {description}".lower()
        
        # Check keywords in order of priority
        for task_type, keywords in self.task_type_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return task_type
        
        # Default to Regular coursework if no keywords match
        return 'Regular coursework'
    
    def calculate_urgency_weight(self, due_date, task_type, estimated_size=None, course_weight=None):
        """
        Calculate urgency weight based on time to deadline with adjustments.
        """
        if due_date is None:
            due_in_days = None
        else:
            # Convert to timezone-aware datetime if needed
            if timezone.is_naive(due_date):
                due_date = timezone.make_aware(due_date)
            
            now = timezone.now()
            time_diff = due_date - now
            due_in_days = math.ceil(time_diff.total_seconds() / (24 * 3600))
        
        # General urgency ladder (baseline)
        if due_in_days is None:
            urgency = 0
        elif due_in_days < 0:  # Overdue
            urgency = 3
        elif due_in_days <= 1:
            urgency = 3
        elif due_in_days <= 3:
            urgency = 2
        elif due_in_days <= 7:
            urgency = 1
        else:  # > 7 days
            urgency = 0
        
        # Adjustments by size/type (deterministic)
        if task_type == 'Major academic' or estimated_size == 'large':
            if due_in_days is not None and due_in_days <= 2:
                urgency = max(urgency, 2)
            if due_in_days is not None and due_in_days <= 7:
                urgency = max(urgency, 3)
        
        if (task_type == 'Regular coursework' and 
            estimated_size == 'small' and 
            due_in_days is not None and due_in_days >= 14):
            urgency = min(urgency, 0)
        
        # Course weight adjustment
        if course_weight is not None and course_weight >= 0.3:
            urgency = min(urgency + 1, 3)  # Cap at 3
        
        return urgency, due_in_days
    
    def apply_moscow_rules(self, task_type, due_in_days, score):
        """
        Apply MoSCoW rules in order, return first match.
        """
        # Rule 1: Hard deadline within 24h always must
        if due_in_days is not None and due_in_days <= 1:
            return 'must', 'Rule 1: Hard deadline within 24h → must'
        
        # Rule 2: Major academic due ≤2 days → must
        if task_type == 'Major academic' and due_in_days is not None and due_in_days <= 2:
            return 'must', 'Rule 2: Major academic due ≤2 days → must'
        
        # Rule 3: Regular coursework due ≤1 days → must
        if task_type == 'Regular coursework' and due_in_days is not None and due_in_days <= 1:
            return 'must', 'Rule 3: Regular coursework due ≤1 days → must'
        
        # Rule 4: Regular coursework due ≤7 days → should
        if task_type == 'Regular coursework' and due_in_days is not None and due_in_days <= 7:
            return 'should', 'Rule 4: Regular coursework due ≤7 days → should'
        
        # Rule 5: Supplementary with deadline ≤1 day → should (never must unless retyped)
        if (task_type == 'Supplementary' and 
            due_in_days is not None and due_in_days <= 1):
            return 'should', 'Rule 5: Supplementary due ≤1 day → should'
        
        # Rule 6: Non-academic → wont
        if task_type == 'Non-academic':
            return 'wont', 'Rule 6: Non-academic → wont'
        
        # Use score thresholds
        if score >= 43:
            return 'must', f'Threshold: score {score} ≥ 43 → must'
        elif score >= 38:
            return 'should', f'Threshold: score {score} 38-42 → should'
        elif score >= 28:
            return 'could', f'Threshold: score {score} 28-37 → could'
        else:
            return 'wont', f'Threshold: score {score} ≤ 27 → wont'
    
    def analyze_tasks(self, tasks_data, now=None, timezone_str='UTC'):
        """
        Main method to analyze tasks and return MoSCoW classification.
        
        Expected input format:
        {
            "now": "2025-09-04T10:00:00Z",
            "timezone": "Asia/Dhaka", 
            "tasks": [
                {
                    "id": "t1",
                    "title": "Final exam: Algorithms",
                    "description": "covers DP and graphs",
                    "due_at": "2025-09-06T09:00:00Z",
                    "estimated_size": "large",  # optional
                    "course_weight": 0.5        # optional
                }
            ]
        }
        """
        if now is None:
            now = timezone.now()
        elif isinstance(now, str):
            now = datetime.fromisoformat(now.replace('Z', '+00:00'))
        
        buckets = {
            'must': [],
            'should': [],
            'could': [],
            'wont': []
        }
        
        decision_log = []
        
        for task_data in tasks_data.get('tasks', []):
            task_id = task_data.get('id', '')
            title = task_data.get('title', '')
            description = task_data.get('description', '')
            due_at = task_data.get('due_at')
            estimated_size = task_data.get('estimated_size')
            course_weight = task_data.get('course_weight')
            
            # Parse due date
            due_date = None
            if due_at:
                try:
                    due_date = datetime.fromisoformat(due_at.replace('Z', '+00:00'))
                except:
                    due_date = None
            
            # 1. Classify task type
            task_type = self.classify_task_type(title, description)
            
            # 2. Get base importance weight
            importance = self.importance_weights[task_type]
            
            # 3. Calculate urgency
            urgency, due_in_days = self.calculate_urgency_weight(
                due_date, task_type, estimated_size, course_weight
            )
            
            # 4. Calculate score
            score = (importance * 10) + (urgency * 3)
            
            # 5. Apply MoSCoW rules
            final_category, matched_rule = self.apply_moscow_rules(task_type, due_in_days, score)
            
            # 6. Create bucket entry
            bucket_entry = {
                'id': task_id,
                'title': title,
                'due_in_days': due_in_days,
                'score': score
            }
            
            buckets[final_category].append(bucket_entry)
            
            # 7. Log decision
            decision_log.append({
                'id': task_id,
                'type': task_type,
                'importance': importance,
                'urgency': urgency,
                'due_in_days': due_in_days,
                'matched_rule': matched_rule,
                'score': score,
                'final': final_category
            })
        
        # Sort buckets for consistency (tie-breaking)
        for category in buckets:
            buckets[category].sort(key=lambda x: (
                x['due_in_days'] if x['due_in_days'] is not None else float('inf'),
                x['title'].casefold(),
                x['id']
            ))
        
        return {
            'generated_at': now.isoformat(),
            'buckets': buckets,
            'decision_log': decision_log
        }
    
    def analyze_django_tasks(self, tasks_queryset, user_timezone='UTC'):
        """
        Analyze Django Task objects and return MoSCoW classification.
        This method converts Django tasks to the expected format and calls analyze_tasks.
        """
        # Convert Django tasks to expected format
        tasks_data = {
            'now': timezone.now().isoformat(),
            'timezone': user_timezone,
            'tasks': []
        }
        
        for task in tasks_queryset:
            task_dict = {
                'id': str(task.id),
                'title': task.title,
                'description': task.description or '',
                'due_at': task.due_date.isoformat() if task.due_date else None,
                # Infer estimated_size from task properties if available
                'estimated_size': getattr(task, 'estimated_size', None),
                # Infer course_weight if available
                'course_weight': getattr(task, 'course_weight', None)
            }
            tasks_data['tasks'].append(task_dict)
        
        return self.analyze_tasks(tasks_data)
