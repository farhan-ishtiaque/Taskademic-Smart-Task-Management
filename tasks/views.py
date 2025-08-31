from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Task, Category, TaskComment, TaskAttachment
from .serializers import (
    TaskSerializer, TaskCreateSerializer, CategorySerializer, 
    TaskCommentSerializer, TaskAttachmentSerializer
)


@login_required
def kanban_board(request):
    """Kanban board view"""
    return render(request, 'tasks/kanban_board.html')


@login_required
def task_calendar(request):
    """Calendar view for tasks"""
    return render(request, 'tasks/calendar.html')


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Task.objects.filter(user=self.request.user)
        
        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by priority
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.select_related('user', 'category').prefetch_related('comments', 'attachments')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TaskCreateSerializer
        return TaskSerializer
    
    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        task = self.get_object()
        task.mark_complete()
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        user_tasks = Task.objects.filter(user=request.user)
        stats = {
            'total': user_tasks.count(),
            'completed': user_tasks.filter(status='done').count(),
            'in_progress': user_tasks.filter(status='in_progress').count(),
            'overdue': sum(1 for task in user_tasks if task.is_overdue),
            'by_priority': dict(
                user_tasks.values('priority').annotate(count=Count('id')).values_list('priority', 'count')
            ),
            'by_status': dict(
                user_tasks.values('status').annotate(count=Count('id')).values_list('status', 'count')
            )
        }
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def kanban_data(self, request):
        user_tasks = Task.objects.filter(user=request.user)
        kanban_data = {
            'todo': TaskSerializer(user_tasks.filter(status='todo'), many=True).data,
            'in_progress': TaskSerializer(user_tasks.filter(status='in_progress'), many=True).data,
            'review': TaskSerializer(user_tasks.filter(status='review'), many=True).data,
            'done': TaskSerializer(user_tasks.filter(status='done'), many=True).data,
        }
        return Response(kanban_data)


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)


class TaskCommentViewSet(viewsets.ModelViewSet):
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        task_id = self.request.query_params.get('task_id')
        if task_id:
            return TaskComment.objects.filter(task_id=task_id)
        return TaskComment.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
