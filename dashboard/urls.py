# In dashboard/urls.py

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # The main productivity dashboard view
    path('', views.dashboard_view, name='dashboard_view'),
    path('goal/new/', views.goal_create_view, name='goal_create'),
    path('goal/<int:goal_id>/edit/', views.goal_update_view, name='goal_edit'),
    path('goal/<int:goal_id>/log/', views.time_log_view, name='time_log'),
    path('goal/<int:goal_id>/reflection/fragment/', views.goal_reflection_fragment_view, name='goal_reflection_fragment'),
    path('goal/<int:goal_id>/delete/', views.goal_delete_view, name='goal_delete'),
]