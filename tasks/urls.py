from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'comments', views.TaskCommentViewSet, basename='comment')

app_name = 'tasks'

urlpatterns = [
    path('api/', include(router.urls)),
    path('kanban/', views.kanban_board, name='kanban_board'),
    path('calendar/', views.task_calendar, name='calendar'),
]
