# In teams/urls.py (New File)

from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    # List all teams the user belongs to
    path('', views.team_list_view, name='team_list'), 
    
    # URL for creating a new team
    path('create/', views.team_create_view, name='team_create'),
    
    # URL for viewing a specific team's details
    path('<int:team_id>/', views.team_dashboard_view, name='team_dashboard'), 

    # New path for creating a goal within a specific team

    path('<int:team_id>/goal/create/', views.team_goal_create_view, name='team_goal_create'),
    path('<int:team_id>/goal/<int:goal_id>/edit/', views.team_goal_edit_view, name='team_goal_edit'),
    path('<int:team_id>/goal/<int:goal_id>/delete/', views.team_goal_delete_view, name='team_goal_delete'),

    path('<int:team_id>/goal/<int:goal_id>/log/', views.team_time_log_create_view, name='team_time_log_create'),

    path('<int:team_id>/goal/<int:goal_id>/', views.team_goal_detail_view, name='team_goal_detail'),

    path('task/<int:task_id>/toggle/', views.team_task_toggle_complete, name='team_task_toggle'),
    # New URL for the Admin Dashboard
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    

    # New path for User Management
    path('admin/users/', views.user_management_view, name='user_management'),

    path('team/<int:team_id>/goals/', views.team_member_tasks_view, name='team_member_tasks'), 
    path('list/', views.team_list_view, name='team_list'),        # New: To show all joinable teams
    path('join/<int:team_id>/', views.team_join_view, name='team_join'), # New: To process joining
    path('remove/<int:team_id>/<int:user_id>/', views.team_remove_view, name='team_remove'), #to process removing a user 

]