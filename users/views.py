from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm

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
