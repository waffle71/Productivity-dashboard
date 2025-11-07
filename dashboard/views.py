from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F
from teams.models import TeamMember
from .models import Goal, TimeLog
from .forms import GoalForm, TimeLogForm
from datetime import timedelta

@login_required
def dashboard_view(request):
    """
    Displays the main productivity dashboard for the logged-in user.
    Shows current goals and progress.
    """
    
    # 1. Fetch the user's current goals
    # We filter goals that are not yet marked as completed
    user_goals = Goal.objects.filter(user=request.user, completed=False).order_by('-importance_level', 'start_date')
    
    # 2. Calculate progress and streaks for each goal
    goals_with_progress = []
    
    for goal in user_goals:
        # Calculate Time Progress
        # Convert total real_time to seconds for calculation
        real_time_seconds = goal.real_time.total_seconds()
        target_time_seconds = goal.target_time.total_seconds()
        
        if target_time_seconds > 0:
            progress_percentage = (real_time_seconds / target_time_seconds) * 100
        else:
            progress_percentage = 0
            
        # Example Streak Logic (Simplistic)
        # This is a basic example; a real streak would be more complex
        current_streak = TimeLog.objects.filter(
            user=request.user, 
            goal=goal
        ).order_by('-log_date').distinct().count() # Counts days with logs
        
        goals_with_progress.append({
            'goal': goal,
            'progress_percentage': round(progress_percentage, 2),
            'current_streak': current_streak
        })


    completed_goals_count = Goal.objects.filter(user=request.user, completed=True).count()
    
    user_teams_membership = TeamMember.objects.filter(
        user=request.user
    ).select_related('team') # Use select_related to fetch Team details efficiently

    context = {
        'goals_with_progress': goals_with_progress,
        'completed_goals_count': completed_goals_count,
        'user_teams': user_teams_membership,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def goal_create_view(request):
    """
    Handles the creation of a new personal goal.
    """
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            # 1. Save the goal instance, but don't commit to the database yet
            goal = form.save(commit=False)
            
            # 2. Assign the logged-in user to the goal
            goal.user = request.user
            
            # 3. Save the instance to the database
            goal.save()
            
            messages.success(request, f"Goal '{goal.title}' created successfully!")
            # Redirect back to the main dashboard
            return redirect('dashboard:dashboard_view')
        else:
            # If form is invalid, messages will be handled in the template
            pass 
    else:
        # GET request: show a blank form
        form = GoalForm()
    
    context = {
        'form': form,
        'page_title': 'Create a New Goal'
    }
    return render(request, 'dashboard/goal_form.html', context)

# In dashboard/views.py (Add the following function)

@login_required
def goal_edit_view(request, goal_id):
    """
    Handles the editing of an existing goal. Requires owner or team admin authorization.
    """
    # 1. Retrieve the goal instance
    goal = get_object_or_404(Goal, pk=goal_id)

    # --- Authorization Check ---
    is_authorized = False
    
    # Check 1: Is the current user the Goal owner?
    if goal.user == request.user:
        is_authorized = True

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

    if not is_authorized:
        messages.error(request, f"You do not have permission to edit the goal '{goal.title}'.")
        return redirect('dashboard:dashboard_view')
    # ---------------------------

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
    goal = get_object_or_404(Goal, pk=goal_id)

    # --- Authorization Check ---
    is_authorized = False
    
    # Check 1: Is the current user the Goal owner? (Applies to all goals)
    if goal.user == request.user:
        is_authorized = True

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
            # User is not a member of the team, so they can't be admin.
            pass

    if not is_authorized:
        messages.error(request, "You do not have permission to delete this goal.")
        return redirect('dashboard:dashboard_view')
    # ---------------------------

    if request.method == 'POST':
        # Deleting a Goal automatically deletes associated TimeLogs (due to CASCADE)
        goal_title = goal.title
        goal.delete()
        messages.success(request, f"Goal '{goal_title}' has been successfully deleted.")
        return redirect('dashboard:dashboard_view')

    # If GET request, show confirmation page (optional, but good practice)
    context = {
        'goal': goal,
        'page_title': f'Confirm Deletion: {goal.title}'
    }
    return render(request, 'dashboard/goal_confirm_delete.html', context)

@login_required
def time_log_view(request, goal_id):
    """
    Handles logging time (Creation) for a specific goal.
    Updates the Goal's 'real_time' field atomically.
    """
    # Ensure the goal exists AND belongs to the logged-in user
    goal = get_object_or_404(Goal, pk=goal_id, user=request.user)
    
    if request.method == 'POST':
        form = TimeLogForm(request.POST)
        if form.is_valid():
            minutes_logged = form.cleaned_data['minutes']
            time_to_add = timedelta(minutes=minutes_logged)
            
            # 1. Save the TimeLog instance
            time_log = form.save(commit=False)
            time_log.goal = goal
            time_log.user = request.user
            time_log.save()
            
            # 2. Atomically Update the Goal's total time (real_time)
            Goal.objects.filter(pk=goal_id).update(
                real_time=F('real_time') + time_to_add
            )
            
            # 3. Check for goal completion (simple check)
            goal.refresh_from_db()
            if goal.real_time >= goal.target_time and not goal.completed:
                 goal.completed = True
                 goal.save(update_fields=['completed'])
                 messages.success(request, f"Congratulations! Goal '{goal.title}' completed!")
            else:
                 messages.success(request, f"Logged {minutes_logged} minutes for '{goal.title}'. Keep it up!")

            return redirect('dashboard:dashboard_view')
    
    form = TimeLogForm()
    context = {
        'goal': goal,
        'form': form,
        'page_title': f'Log Time for: {goal.title}'
    }
    return render(request, 'dashboard/time_log_form.html', context)

@login_required
def time_log_edit_view(request, log_id):
    """
    Handles editing an existing TimeLog entry.
    Requires complex logic to subtract old time and add new time to the parent Goal.
    """
    # Get the existing log and ensure it belongs to the user
    log_instance = get_object_or_404(TimeLog, pk=log_id, user=request.user)
    goal = log_instance.goal # Parent Goal
    
    if request.method == 'POST':
        form = TimeLogForm(request.POST, instance=log_instance)
        if form.is_valid():
            # Old time logged, before form save
            minutes_old = log_instance.minutes
            minutes_new = form.cleaned_data['minutes']
            
            # Calculate the difference in time to adjust the Goal total
            minutes_delta = minutes_new - minutes_old
            time_delta = timedelta(minutes=minutes_delta)

            with transaction.atomic():
                # 1. Update the Goal's total time atomically
                Goal.objects.filter(pk=goal.id).update(
                    real_time=F('real_time') + time_delta
                )
                
                # 2. Save the updated TimeLog instance
                form.save()

                # 3. Re-check for goal completion
                goal.refresh_from_db()
                if goal.real_time >= goal.target_time and not goal.completed:
                    goal.completed = True
                    goal.save(update_fields=['completed'])
                    messages.success(request, f"Goal '{goal.title}' completed after log update!")

                messages.success(request, f"Time log updated from {minutes_old}m to {minutes_new}m.")
                return redirect('dashboard:dashboard_view')
    else:
        form = TimeLogForm(instance=log_instance)
    
    context = {
        'form': form,
        'goal': goal,
        'page_title': f'Edit Log: {log_instance}'
    }
    return render(request, 'dashboard/time_log_form.html', context)

@login_required
@transaction.atomic # Ensure Goal update and Log deletion happen together
def time_log_delete_view(request, log_id):
    """
    Handles deletion of a TimeLog entry. Atomically subtracts time from the parent Goal.
    """
    # Get the existing log and ensure it belongs to the user
    log_instance = get_object_or_404(TimeLog, pk=log_id, user=request.user)
    goal = log_instance.goal # Parent Goal
    minutes_to_subtract = log_instance.minutes
    time_to_subtract = timedelta(minutes=minutes_to_subtract)

    if request.method == 'POST':
        # 1. Atomically subtract the time from the Goal's total
        Goal.objects.filter(pk=goal.id).update(
            real_time=F('real_time') - time_to_subtract
        )
        
        # 2. Delete the TimeLog
        log_instance.delete()
        
        # 3. If goal was completed, check if it should now be incomplete
        goal.refresh_from_db()
        if goal.completed and goal.real_time < goal.target_time:
            goal.completed = False
            goal.save(update_fields=['completed'])
            messages.warning(request, f"Goal '{goal.title}' is now incomplete after log removal.")

        messages.success(request, f"Time log of {minutes_to_subtract} minutes deleted.")
        return redirect('dashboard:dashboard_view')

    # Confirmation page on GET request
    context = {
        'log_instance': log_instance,
        'goal': goal,
        'page_title': f'Confirm Deletion of Time Log: {log_instance.minutes}m'
    }
    return render(request, 'dashboard/time_log_confirm_delete.html', context)

@login_required
def goal_reflection_fragment_view(request, goal_id): # Renamed function
    """
    Returns only the HTML fragment (content) needed for the reflection modal.
    """
    # Ensure the goal exists AND belongs to the logged-in user
    goal = get_object_or_404(Goal, pk=goal_id, user=request.user)
    
    # Calculate progress for display
    real_time_seconds = goal.real_time.total_seconds()
    target_time_seconds = goal.target_time.total_seconds()
    
    progress_percentage = 0
    if target_time_seconds > 0:
        progress_percentage = round((real_time_seconds / target_time_seconds) * 100, 2)
        
    time_logs = TimeLog.objects.filter(
        user=request.user, 
        goal=goal
    ).order_by('-log_date', '-minutes') 
    
    context = {
        'goal': goal,
        'progress_percentage': progress_percentage,
        'time_logs': time_logs,
    }
    
    # Render only the fragment template
    return render(request, 'dashboard/reflection_fragment.html', context)