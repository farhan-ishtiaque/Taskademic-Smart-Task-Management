from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.team_list, name='list'),
    path('status/', views.team_status, name='status'),  # Debug status page
    path('create/', views.team_create, name='create'),
    path('<uuid:team_id>/', views.team_detail, name='detail'),
    path('<uuid:team_id>/members/', views.team_members_json, name='members_json'),  # For AJAX
    path('<uuid:team_id>/invite-status/', views.check_invite_status, name='invite_status'),  # Check invites and tasks
    
    # Simple email invite only
    path('<uuid:team_id>/invite/email/', views.team_invite_email, name='invite_email'),
    path('<uuid:team_id>/cancel-invite/<uuid:invite_id>/', views.cancel_invite, name='cancel_invite'),
    path('accept-invite/<str:invite_token>/', views.accept_invite, name='accept_invite'),
]
