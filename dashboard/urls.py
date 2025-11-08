# In dashboard/urls.py

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # The main productivity dashboard view
    path('', views.dashboard_view, name='dashboard_view'),
    path('goal/new/', views.goal_create_view, name='goal_create'),
    path('goal/<int:goal_id>/edit/', views.goal_edit_view, name='goal_edit'),
    path('goal/<int:goal_id>/delete/', views.goal_delete_view, name='goal_delete'),
    path('log-time/<int:goal_id>/', views.time_log_view, name='time_log'), 
    path('goals/<int:goal_id>/reflection/', views.goal_reflection_fragment, name='goal_reflection_fragment'),
]
