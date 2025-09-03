from django.urls import path
from . import views

app_name = 'points'

urlpatterns = [
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('profile/', views.profile_view, name='profile'),
    path('achievements/', views.achievements_view, name='achievements'),
    
    # API endpoints
    path('api/stats/', views.user_stats_api, name='api_stats'),
    path('api/widget/', views.points_widget_data, name='api_widget'),
]
