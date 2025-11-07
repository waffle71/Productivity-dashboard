from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F
from teams.models import TeamMember
from .models import Goal, TimeLog
from .forms import GoalForm, TimeLogForm
from datetime import timedelta


def _update_goal_progress(goal: Goal) -> Goal:
    """Refresh goal progress and completion status after time adjustments."""

    goal.refresh_from_db()

    fields_to_update = set()

    if goal.real_time < timedelta(0):
        goal.real_time = timedelta(0)
        fields_to_update.add('real_time')

    if goal.real_time >= goal.target_time:
        if not goal.completed:
            goal.completed = True
            fields_to_update.add('completed')
    else:
        if goal.completed:
            goal.completed = False
            fields_to_update.add('completed')

    if fields_to_update:
        goal.save(update_fields=list(fields_to_update))

    return goal

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

    # context = {
    #     'goals_with_progress': goals_with_progress,
    #     'completed_goals_count': Goal.objects.filter(user=request.user, completed=True).count(),
    #     # We can add motivational content here (Admin features)
    # }
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
            form.save_m2m()
            
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
        'page_title': 'Create a New Goal',
        'is_edit': False,
    }
    return render(request, 'dashboard/goal_form.html', context)


@login_required
def goal_update_view(request, goal_id):
    """Allow users to edit an existing personal goal."""

    goal = get_object_or_404(Goal, pk=goal_id, user=request.user)

    if request.method == 'POST':
        form = GoalForm(request.POST, instance=goal)
        if form.is_valid():
            updated_goal = form.save(commit=False)
            # Ensure ownership stays with the logged-in user
            updated_goal.user = request.user
            updated_goal.save()
            form.save_m2m()

            messages.success(request, f"Goal '{updated_goal.title}' updated successfully!")
            return redirect('dashboard:dashboard_view')
    else:
        form = GoalForm(instance=goal)

    context = {
        'form': form,
        'page_title': f"Edit Goal: {goal.title}",
        'is_edit': True,
    }

    return render(request, 'dashboard/goal_form.html', context)

@login_required
def time_log_view(request, goal_id):
    """
    Handles logging time for a specific goal (Goal_id).
    It also updates the Goal's 'real_time' field atomically.
    """
    # Ensure the goal exists AND belongs to the logged-in user
    goal = get_object_or_404(Goal, pk=goal_id, user=request.user)
    was_completed = goal.completed

    if request.method == 'POST':
        form = TimeLogForm(request.POST)
        if form.is_valid():
            minutes_logged = form.cleaned_data['minutes']

            # 1. Save the TimeLog instance
            time_log = form.save(commit=False)
            time_log.goal = goal
            time_log.user = request.user
            time_log.save()

            # 2. Update the Goal's total time (real_time)
            # Use F expression for atomic update to prevent race conditions
            time_to_add = timedelta(minutes=minutes_logged)

            Goal.objects.filter(pk=goal_id).update(
                real_time=F('real_time') + time_to_add
            )

            # 3. Refresh goal progress and completion state
            goal = _update_goal_progress(goal)

            if goal.completed and not was_completed:
                messages.success(request, f"Congratulations! Goal '{goal.title}' completed!")
            else:
                messages.success(request, f"Logged {minutes_logged} minutes for '{goal.title}'. Keep it up!")

            # Redirect back to the main dashboard
            return redirect('dashboard:dashboard_view')

    # GET request: show the log form
    form = TimeLogForm()

    context = {
        'goal': goal,
        'form': form,
        'page_title': f'Log Time for: {goal.title}',
        'is_edit': False,
        'time_log': None,
    }

    # We will use the same template as the goal form, but with a different context
    return render(request, 'dashboard/time_log_form.html', context)


@login_required
def time_log_update_view(request, goal_id, log_id):
    """Allow users to update an existing time log for a goal."""

    goal = get_object_or_404(Goal, pk=goal_id, user=request.user)
    time_log = get_object_or_404(TimeLog, pk=log_id, goal=goal, user=request.user)
    was_completed = goal.completed
    original_minutes = time_log.minutes

    if request.method == 'POST':
        form = TimeLogForm(request.POST, instance=time_log)
        if form.is_valid():
            updated_log = form.save(commit=False)
            updated_log.goal = goal
            updated_log.user = request.user

            updated_minutes = updated_log.minutes
            minute_difference = updated_minutes - original_minutes

            updated_log.save()

            if minute_difference != 0:
                time_delta = timedelta(minutes=minute_difference)
                Goal.objects.filter(pk=goal.pk).update(
                    real_time=F('real_time') + time_delta
                )

            goal = _update_goal_progress(goal)

            if minute_difference == 0:
                messages.info(request, "No changes were made to the time log.")
            elif goal.completed and not was_completed:
                messages.success(request, f"Congratulations! Goal '{goal.title}' completed!")
            elif not goal.completed and was_completed:
                messages.info(
                    request,
                    f"Goal '{goal.title}' is back in progress after updating the time log to {updated_minutes} minutes.",
                )
            else:
                messages.success(
                    request,
                    f"Updated time log to {updated_minutes} minutes for '{goal.title}'.",
                )

            return redirect('dashboard:dashboard_view')
    else:
        form = TimeLogForm(instance=time_log)

    context = {
        'goal': goal,
        'form': form,
        'page_title': f'Edit Time Log for: {goal.title}',
        'is_edit': True,
        'time_log': time_log,
    }

    return render(request, 'dashboard/time_log_form.html', context)


@login_required
def time_log_delete_view(request, goal_id, log_id):
    """Confirm and delete an existing time log for a goal."""

    goal = get_object_or_404(Goal, pk=goal_id, user=request.user)
    time_log = get_object_or_404(TimeLog, pk=log_id, goal=goal, user=request.user)
    was_completed = goal.completed

    if request.method == 'POST':
        minutes_removed = time_log.minutes
        time_log.delete()

        Goal.objects.filter(pk=goal.pk).update(
            real_time=F('real_time') - timedelta(minutes=minutes_removed)
        )

        goal = _update_goal_progress(goal)

        messages.success(
            request,
            f"Deleted the {minutes_removed}-minute time log for '{goal.title}'.",
        )

        if goal.completed and not was_completed:
            messages.success(request, f"Congratulations! Goal '{goal.title}' completed!")
        elif not goal.completed and was_completed:
            messages.info(request, f"Goal '{goal.title}' is back in progress after removing the time log.")

        return redirect('dashboard:dashboard_view')

    context = {
        'goal': goal,
        'time_log': time_log,
        'page_title': f'Delete Time Log for: {goal.title}',
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