from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, TimeBlock


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class TaskSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    tag_list = serializers.ListField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'due_date', 'estimated_duration',
            'priority', 'status', 'category', 'tags', 'points_awarded',
            'created_at', 'updated_at', 'completed_at', 'user', 'tag_list', 'is_overdue'
        ]
        read_only_fields = ('user', 'points_awarded', 'created_at', 'updated_at', 'completed_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'due_date', 'estimated_duration',
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
