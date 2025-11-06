# In users/decorators.py (New File)

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    """
    Decorator to check if the user is logged in AND has the 'ADMIN' role.
    If not, redirects them to the dashboard or shows a 403 error.
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # If not logged in, redirect to login page
            messages.error(request, "You must be logged in to access this page.")
            return redirect('users:login') 
        
        # Check the custom 'role' field
        if request.user.role != 'ADMIN':
            # If logged in but not an Admin, deny access
            messages.error(request, "You do not have administrative privileges.")
            # Optionally redirect to their main dashboard instead of 403
            return redirect('dashboard:dashboard_view') 
            
        return view_func(request, *args, **kwargs)
        
    return wrapper