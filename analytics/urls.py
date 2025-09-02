from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Web views
    path('', views.analytics_dashboard, name='dashboard'),
    
    # Combined API endpoint
    path('api/', views.analytics_api, name='api'),
    
    # Individual API endpoints
    path('api/daily-progress/', views.daily_progress, name='api_daily_progress'),
    path('api/weekly-category-stats/', views.weekly_category_stats, name='api_weekly_category_stats'),
    path('api/priority-breakdown/', views.priority_breakdown, name='api_priority_breakdown'),
    path('api/productivity-trends/', views.productivity_trends, name='api_productivity_trends'),
    path('api/user-points-level/', views.user_points_level, name='api_user_points_level'),
    path('api/overdue-analysis/', views.overdue_analysis, name='api_overdue_analysis'),
    path('api/summary/', views.analytics_summary, name='api_summary'),
]
