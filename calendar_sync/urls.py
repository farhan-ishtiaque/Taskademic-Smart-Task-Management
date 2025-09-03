from django.urls import path
from . import views

app_name = 'calendar_sync'

urlpatterns = [
    path('settings/', views.calendar_settings, name='settings'),
    path('connect/', views.connect_calendar, name='connect'),
    path('oauth/callback/', views.oauth_callback, name='oauth_callback'),
    path('toggle-sync/', views.toggle_sync, name='toggle_sync'),
    path('disconnect/', views.disconnect_calendar, name='disconnect'),
    path('status/', views.sync_status, name='status'),
    path('force-sync/<int:task_id>/', views.force_sync_task, name='force_sync_task'),
]
