from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from .models import Notification

# Create your views here.
def register_view(request):
    """
    Handle new user registration.
    """
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect("dashboard:dashboard_view")
        else:
            messages.error(request, "Unsuccessful registration. Invalid information.")
    else:
        form = CustomUserCreationForm()

    return render(request, "users/register.html", context={"form":form})

def login_view(request):
    """
    Handle user login.
    """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request,username = username,password=password)

            if user is not None:
                login(request, user)
                messages.info(request, f"Welcome back, {username}.")
                return redirect("dashboard:dashboard_view")
            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request, "Invalivd username or password")
    form = AuthenticationForm()
    return render(request, "users/login.html", context={"form": form})

@login_required
def mark_notification_as_read(request, notification_id):
    """
    Marks a specific notification as 'read' and redirects
    the user to the notification's link.
    """
    # Find the notification, ensuring it belongs to the current user
    notification = get_object_or_404(
        Notification, 
        pk=notification_id, 
        user=request.user
    )
    
    # Mark it as read
    notification.is_read = True
    notification.save()
    
    # Redirect to the link (e.g., the team goal detail page)
    # If there's no link, just go to the dashboard
    if notification.link:
        return redirect(notification.link)
    else:
        return redirect('dashboard:dashboard_view')