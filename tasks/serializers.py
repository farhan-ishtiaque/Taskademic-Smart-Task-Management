from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, TimeBlock


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class TaskSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    assigned_to_display = serializers.SerializerMethodField()
    tag_list = serializers.ListField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    is_assigned = serializers.BooleanField(read_only=True)
    assignment_status = serializers.CharField(read_only=True)
    moscow_category = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'due_date', 'reminder_minutes',
            'priority', 'status', 'category', 'tags', 'points_awarded',
            'created_at', 'updated_at', 'completed_at', 'user', 'assigned_to',
            'assigned_to_display', 'tag_list', 'is_overdue', 'is_assigned', 'assignment_status',
            'moscow_category'
        ]
        read_only_fields = ('user', 'points_awarded', 'created_at', 'updated_at', 'completed_at')
    
    def get_moscow_category(self, obj):
        """Get MoSCoW category for the task"""
        # Get the actual MoSCoW analysis instead of basic priority
        from priority_analyzer.signals import MoSCoWCacheService
        
        # Get user from context
        request = self.context.get('request')
        if not request or not request.user:
            return 'Should Have'
            
        try:
            # Get the full MoSCoW analysis for the user
            result = MoSCoWCacheService.get_moscow_analysis(request.user)
            
            # Find this task in the decision log
            for log_entry in result.get('decision_log', []):
                if int(log_entry['id']) == obj.id:
                    return log_entry['final']
        except Exception:
            pass
        
        # Fallback based on task content analysis
        title_lower = obj.title.lower()
        if 'exam' in title_lower or 'quiz' in title_lower or 'test' in title_lower:
            return 'Must Have'
        elif 'assignment' in title_lower or 'project' in title_lower:
            return 'Should Have'
        else:
            return 'Could Have'
    
    def get_assigned_to_display(self, obj):
        if obj.assigned_to:
            if obj.assigned_to.first_name and obj.assigned_to.last_name:
                return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}"
            return obj.assigned_to.username
        return None

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'due_date', 'reminder_minutes',
            'priority', 'status', 'category', 'tags'
        ]


class TimeBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeBlock
        fields = '__all__'
        read_only_fields = ('user',)


class KanbanBoardSerializer(serializers.Serializer):
    todo = TaskSerializer(many=True, read_only=True)
    in_progress = TaskSerializer(many=True, read_only=True)
    done = TaskSerializer(many=True, read_only=True)
