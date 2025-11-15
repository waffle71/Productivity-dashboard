from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    #path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/user/<int:user_id>/', views.admin_user_detail_view, name='admin_user_detail'),
    path('admin-dashboard/user/<int:user_id>/change-password/', views.admin_change_password_view, name='admin_change_password'),
]