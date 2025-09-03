from django.urls import path
from . import views

app_name = 'priority_analyzer'

urlpatterns = [
    path('analyze/', views.analyze_priority, name='analyze_priority'),
]
