from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'timeblocks', views.TimeBlockViewSet, basename='timeblock')

app_name = 'tasks'

urlpatterns = [
    # Web views
    path('', views.task_list, name='list'),
    path('create/', views.task_create, name='create'),
    path('edit/', views.task_edit_select, name='edit_select'),
    path('edit/<int:task_id>/', views.task_edit, name='edit'),
    path('complete/<int:task_id>/', views.task_complete, name='complete'),
    path('kanban/', views.kanban_board, name='kanban_board'),
    path('team/<uuid:team_id>/kanban/', views.team_kanban_board, name='team_kanban_board'),
    path('calendar/', views.task_calendar, name='calendar'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/statistics/', views.task_statistics, name='api_statistics'),
    path('api/schedule/suggestions/', views.smart_schedule_suggestion, name='api_schedule_suggestions'),
    path('api/teams/<uuid:team_id>/members/', views.get_team_members, name='api_team_members'),
]
