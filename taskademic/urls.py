"""
URL configuration for taskademic project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.generic import TemplateView

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    else:
        return redirect('accounts:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('dashboard/', include('dashboard.urls')),
    path('tasks/', include('tasks.urls')),
    path('analytics/', include('analytics.urls')),
    path('accounts/', include('accounts.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('priority/', include('priority_analyzer.urls')),
    path('calendar-sync/', include('calendar_sync.urls')),
    path('points/', include('points.urls')),
    path('debug/firebase-test/', TemplateView.as_view(template_name='debug/firebase_test.html'), name='firebase_test'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
