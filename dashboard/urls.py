from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('settings/', views.settings_view, name='settings'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('daily-routine/', views.daily_routine, name='daily_routine'),
    path('moscow-matrix/', views.moscow_matrix, name='moscow_matrix'),
    path('focus-timer/', views.focus_timer, name='focus_timer'),
]
