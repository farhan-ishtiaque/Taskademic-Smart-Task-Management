from django.urls import path
from . import views
from .focus_timer import focus_timer, complete_task_ajax, update_timer_session
from .moscow_matrix import refresh_moscow_matrix

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('settings/', views.settings_view, name='settings'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('daily-routine/', views.daily_routine, name='daily_routine'),
    path('moscow-matrix/', views.moscow_matrix, name='moscow_matrix'),
    path('focus-timer/', focus_timer, name='focus_timer'),
    
    # AJAX endpoints for focus timer
    path('ajax/complete-task/', complete_task_ajax, name='complete_task_ajax'),
    path('ajax/timer-session/', update_timer_session, name='update_timer_session'),
    
    # MoSCoW matrix endpoints
    path('ajax/refresh-moscow/', refresh_moscow_matrix, name='refresh_moscow_matrix'),
    
    # Daily Schedule endpoints
    path('daily-schedule/', views.daily_schedule_home, name='daily_schedule_home'),
    path('time-blocks/', views.manage_time_blocks, name='manage_time_blocks'),
    path('time-blocks/add/', views.add_time_block, name='add_time_block'),
    path('time-blocks/delete/<int:block_id>/', views.delete_time_block, name='delete_time_block'),
    path('time-blocks/edit/<int:block_id>/', views.edit_time_block, name='edit_time_block'),
    path('schedule/generate/', views.generate_schedule, name='generate_schedule'),
    path('schedule/view/<int:year>/<int:month>/<int:day>/', views.view_schedule, name='view_schedule'),
    path('schedule/history/', views.schedule_history, name='schedule_history'),
    path('custom-schedule/', views.create_custom_schedule, name='create_custom_schedule'),
    path('ajax/mark-completed/<int:task_id>/', views.mark_task_completed, name='mark_task_completed'),
]
