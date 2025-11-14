from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from .models import PersonalGoal, PersonalTimeLog
from .forms import GoalForm, TimeLogForm
from datetime import timedelta, date
from users.decorators import admin_required

def index_view(request):
    """
    Redirects the user to the dashboard if they are logged in,
    or to the login page if they are not.
    """
    if request.user.is_authenticated:
        # Redirect to your main dashboard's URL name
        return redirect('dashboard:dashboard_view')
    else:
        # Redirect to your login page's URL name
        return redirect('login')
    
@login_required
def dashboard_view(request):
    # Fetch all personal goals for the logged-in user
    user_goals = PersonalGoal.objects.filter(user=request.user).order_by('-created_at')
    
    goals_with_progress = []
    completed_goals_count = 0
    
    today = date.today()
    
    for goal in user_goals:
        # Progress Calculation (Kept as is)
        # Convert target and real time from timedelta to minutes
        target_time_minutes = goal.target_time.total_seconds() / 60 if goal.target_time else 0
        real_time_minutes = goal.real_time.total_seconds() / 60 if goal.real_time else 0
        
        # Calculate progress percentage, capped at 100%
        if target_time_minutes > 0:
            progress_percentage = min(100, int((real_time_minutes / target_time_minutes) * 100))
        else:
            progress_percentage = 0

        # Count completed goals
        if goal.completed:
            completed_goals_count += 1
            
        # Streak Calculation 
        current_streak = 0
        
        # Get distinct log dates for this goal using .dates() for SQLite compatibility
        goal_log_dates = PersonalTimeLog.objects.filter(
            goal=goal
        ).dates('log_date', 'day') 
        logged_dates_set = set(goal_log_dates)
        
        # Start checking from today
        check_date = today
        
        # Start checking from today; fallback to yesterday if today is not logged
        if today not in logged_dates_set:
            check_date = today - timedelta(days=1)
        
        # Count consecutive logged days backwards
        while check_date in logged_dates_set:
            current_streak += 1
            check_date -= timedelta(days=1)
        
        # Append goal data to the list
        goals_with_progress.append({
            'goal': goal,
            'progress_percentage': progress_percentage,
            'current_streak': current_streak,
            'real_time_minutes': real_time_minutes,
            'target_time_minutes': target_time_minutes,
        })

    # Get all teams the user is a member of
    user_teams = request.user.teammember_set.all()

    # Prepare context for rendering the dashboard
    context = {
        'goals_with_progress': goals_with_progress,
        'completed_goals_count': completed_goals_count,
        'user_teams': user_teams,
    }
    # Render the dashboard template with context
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def goal_create_view(request):
    """
    Handles the goal creation.
    """
    # Handle form submission
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False) # Don't save to DB yet
            goal.user = request.user # Assign current user as user
            goal.save() # Save to DB
            messages.success(request, f" Goal “{goal.title}” created successfully!")
            return redirect('dashboard:dashboard_view')
    else:
        # If it is a GET request, show empty form
        form = GoalForm()

    # Render goal creation form
    return render(request, 'dashboard/goal_form.html', {
        'form': form,
        'page_title': 'Create a New Goal',
        'is_edit': False,
    })

@login_required
def goal_edit_view(request, goal_id):
    """
    Handles the editing of an existing goal. Requires owner or team admin authorization.
    """
    # 1. Retrieve the goal instance
    goal = get_object_or_404(PersonalGoal, pk=goal_id)

    # Authorization check
    is_authorized = False
    
    # Is the current user the Goal owner?
    if goal.user == request.user:
        is_authorized = True
    
    """
    # Check 2: Is this a Team Goal, and is the user a Team Admin?
    if hasattr(goal, 'teamgoal') and goal.teamgoal.team:
        try:
            member_role = TeamMember.objects.get(
                user=request.user, 
                team=goal.teamgoal.team
            ).role
            if member_role == TeamMember.Role.ADMIN:
                is_authorized = True
        except TeamMember.DoesNotExist:
            pass # Not a member, so not an admin

    """    
    if not is_authorized:
        messages.error(request, f"You do not have permission to edit the goal '{goal.title}'.")
        return redirect('dashboard:dashboard_view')
    
    if request.method == 'POST':
        # Instantiate the form with POST data AND the existing goal instance
        form = GoalForm(request.POST, instance=goal)
        if form.is_valid():
            # Form saves changes directly to the 'instance=goal' object
            form.save()
            messages.success(request, f"Goal '{goal.title}' updated successfully!")
            return redirect('dashboard:dashboard_view')
    else:
        # GET request: Instantiate the form with the existing goal data
        form = GoalForm(instance=goal)
    
    context = {
        'form': form,
        'page_title': f'Edit Goal: {goal.title}'
    }
    # Reuse the goal creation template
    return render(request, 'dashboard/goal_form.html', context)

@login_required
def goal_delete_view(request, goal_id):
    """
    Handles deletion of a Goal. Checks for ownership/admin status before deleting.
    """
    goal = get_object_or_404(PersonalGoal, pk=goal_id)

    # Authorization Check
    is_authorized = False
    
    # Is the current user the Goal owner? 
    if goal.user == request.user:
        is_authorized = True

    if not is_authorized:
        messages.error(request, "You do not have permission to delete this goal.")
        return redirect('dashboard:dashboard_view')
    else:
        goal_title = goal.title
        goal.delete()
        messages.success(request, f"Goal '{goal_title}' has been successfully deleted.")
        return redirect('dashboard:dashboard_view')

@login_required
def time_log_view(request, goal_id):
    """
    Handles logging time (Creation) for a specific goal.
    Updates the Goal's 'real_time' field atomically.
    """
    goal = get_object_or_404(PersonalGoal, pk=goal_id, user=request.user)

    if request.method == 'POST':
        form = TimeLogForm(request.POST)
        if form.is_valid():
            minutes_logged = float(form.cleaned_data['minutes'])
            with transaction.atomic():
                time_log = form.save(commit=False)
                time_log.goal = goal
                time_log.user = request.user
                time_log.minutes = int(round(minutes_logged))  # if TimeLog.minutes is IntegerField
                time_log.save() # Observer
                

            goal.refresh_from_db(fields=['real_time', 'completed', 'target_time'])
            
            if goal.target_time and goal.real_time >= goal.target_time and not goal.completed:
                goal.completed = True
                goal.save(update_fields=['completed'])
                messages.success(request, f"🎉 Congratulations! Goal '{goal.title}' completed!")
            else:
                messages.success(request, f"✅ Logged {time_log.minutes} minutes for '{goal.title}'. Keep it up!")
            
            return redirect('dashboard:dashboard_view')
    else:
        form = TimeLogForm(initial={'log_date': date.today()})

    context = {
        'goal': goal,
        'form': form,
        'page_title': f'Log Time for: {goal.title}',
    }
    return render(request, 'dashboard/time_log_form.html', context)


@login_required
def goal_reflection_fragment(request, goal_id):
    """
    Fetches and renders an HTML fragment for the reflection modal.
    This view is called via JavaScript (Fetch API).
    """
    # 1. Get the goal, ensuring it belongs to the logged-in user for security.
    goal = get_object_or_404(PersonalGoal, id=goal_id, user=request.user)
    
    # 2. Get all related time logs, ordered most recent first.
    time_logs = goal.time_logs.all().order_by('-log_date', '-created_at')
    
    # 3. Calculate summary statistics
    total_logs = time_logs.count()
    total_minutes = sum(log.minutes for log in time_logs)
    total_hours = total_minutes / 60.0
    
    context = {
        'goal': goal,
        'time_logs': time_logs,
        'total_logs': total_logs,
        'total_minutes': total_minutes,
        'total_hours': total_hours,
    }
    
    # 4. Render the HTML fragment (not a full page)
    return render(request, 'dashboard/fragments/goal_reflection_fragment.html', context)


