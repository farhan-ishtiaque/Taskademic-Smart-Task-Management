from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('mark-read/<uuid:notification_id>/', views.mark_as_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('accept-invite/<uuid:notification_id>/', views.accept_team_invite_notification, name='accept_team_invite'),
    path('unread-count/', views.get_unread_count, name='unread_count'),
    path('recent/', views.get_recent_notifications, name='recent'),
    path('debug/', views.debug_notifications, name='debug'),
    path('preferences/update/', views.update_preferences, name='update_preferences'),
    path('preferences/', views.get_preferences, name='get_preferences'),
]
