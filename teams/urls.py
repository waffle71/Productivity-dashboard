# In teams/urls.py (New File)

from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    # List all teams the user belongs to
    path('', views.team_list_view, name='team_list'), 
    
    # URL for creating a new team
    path('new/', views.team_create_view, name='team_create'),
    
    # URL for viewing a specific team's details
    path('<int:team_id>/', views.team_detail_view, name='team_detail'), 

    # New path for creating a goal within a specific team
    path('<int:team_id>/goal/new/', views.team_goal_create_view, name='team_goal_create'),

    # New URL for the Admin Dashboard
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    
    # New path for User Management
    path('admin/users/', views.user_management_view, name='user_management'),

    path('team/<int:team_id>/', views.team_dashboard_view, name='team_dashboard'),
    path('team/<int:team_id>/goals/', views.team_member_tasks_view, name='team_member_tasks'), 

]