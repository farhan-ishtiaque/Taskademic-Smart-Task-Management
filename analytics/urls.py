from django.urls import path
from . import views
from . import debug_views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('api/', views.analytics_api, name='api'),
    path('debug/', debug_views.analytics_debug, name='debug'),
    path('status/', views.system_status, name='status'),
]
