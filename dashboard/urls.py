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
]
