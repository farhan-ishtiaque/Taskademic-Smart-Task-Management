from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Web views
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # API endpoints
    path('api/register/', views.register_user, name='api_register'),
    path('api/login/', views.login_user, name='api_login'),
    path('api/logout/', views.logout_user, name='api_logout'),
    path('api/profile/', views.user_profile, name='api_profile'),
    path('api/stats/', views.user_stats, name='api_stats'),
]
