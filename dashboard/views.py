from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from teams.models import TeamMember
from .models import Goal, TimeLog
from .forms import GoalForm, TimeLogForm
from datetime import timedelta, date

@login_required
def dashboard_view(request):
    # Fetch all personal goals for the logged-in user
    user_goals = Goal.objects.filter(user=request.user).order_by('-created_at')
    
    goals_with_progress = []
    completed_goals_count = 0
    
    today = date.today()
    
    for goal in user_goals:
        # Progress Calculation (Kept as is)
        target_time_minutes = goal.target_time.total_seconds() / 60 if goal.target_time else 0
        real_time_minutes = goal.real_time.total_seconds() / 60 if goal.real_time else 0
        
        if target_time_minutes > 0:
            progress_percentage = min(100, int((real_time_minutes / target_time_minutes) * 100))
        else:
            progress_percentage = 0

        if goal.completed:
            completed_goals_count += 1
            
        # --- ADVANCED STREAK CALCULATION (FIXED LOGIC) ---
        current_streak = 0
        
        #  FIX: Use the .dates() method for safe, distinct date extraction 
        # from the 'log_date' DateTimeField, filtered only for the current goal.
        # This is the most reliable method for SQLite.
        goal_log_dates = TimeLog.objects.filter(
            goal=goal
        ).dates('log_date', 'day') # Returns a QuerySet of datetime.date objects

        # Convert the QuerySet of dates into a set for fast lookup
        logged_dates_set = set(goal_log_dates)
        
        # Start checking from today
        check_date = today
        
        # Check if the user logged today
        if today not in logged_dates_set:
            # If they didn't log today, check yesterday. If yesterday is also missing,
            # the streak is zero, and the loop below won't execute.
            check_date = today - timedelta(days=1)
        
        # Check consecutive days backward
        # The loop condition is implicitly false if check_date is not in the set
        # (e.g., if today and yesterday were both skipped).
        while check_date in logged_dates_set:
            current_streak += 1
            check_date -= timedelta(days=1)
        # --- END ADVANCED STREAK CALCULATION ---

        goals_with_progress.append({
            'goal': goal,
            'progress_percentage': progress_percentage,
            'current_streak': current_streak,
        })

    # ... (rest of the code for teams and context)
    user_teams = request.user.teammember_set.all()

    context = {
        'goals_with_progress': goals_with_progress,
        'completed_goals_count': completed_goals_count,
        'user_teams': user_teams,
    }
    return render(request, 'dashboard/dashboard.html', context)

# @login_required
# def goal_create_view(request):
#     """
#     Handles the creation of a new personal goal.
#     """
#     if request.method == 'POST':
#         form = GoalForm(request.POST)
#         if form.is_valid():
#             # 1. Save the goal instance, but don't commit to the database yet
#             goal = form.save(commit=False)
            
#             # 2. Assign the logged-in user to the goal
#             goal.user = request.user
            
#             # 3. Save the instance to the database
#             goal.save()
            
#             messages.success(request, f"Goal '{goal.title}' created successfully!")
#             # Redirect back to the main dashboard
#             return redirect('dashboard:dashboard_view')
#         else:
#             # If form is invalid, messages will be handled in the template
#             pass 
#     else:
#         # GET request: show a blank form
#         form = GoalForm()
    
#     context = {
#         'form': form,
#         'page_title': 'Create a New Goal'
#     }
#     return render(request, 'dashboard/goal_form.html', context)

# In dashboard/views.py (Add the following function)
@login_required
def goal_create_view(request):
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, f" Goal “{goal.title}” created successfully!")
            return redirect('dashboard:dashboard_view')
    else:
        form = GoalForm()

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
    # if hasattr(goal, 'teamgoal') and goal.teamgoal.team:
    #     try:
    #         member_role = TeamMember.objects.get(
    #             user=request.user, 
    #             team=goal.teamgoal.team
    #         ).role
    #         if member_role == TeamMember.Role.ADMIN:
    #             is_authorized = True
    #     except TeamMember.DoesNotExist:
    #         # User is not a member of the team, so they can't be admin.
    #         pass

    if not is_authorized:
        messages.error(request, "You do not have permission to delete this goal.")
        return redirect('dashboard:dashboard_view')
    else:
        goal_title = goal.title
        goal.delete()
        messages.success(request, f"Goal '{goal_title}' has been successfully deleted.")
        return redirect('dashboard:dashboard_view')

    # ---------------------------

    # if request.method == 'POST':
    #     # Deleting a Goal automatically deletes associated TimeLogs (due to CASCADE)
    #     goal_title = goal.title
    #     goal.delete()
    #     messages.success(request, f"Goal '{goal_title}' has been successfully deleted.")
    #     return redirect('dashboard:dashboard_view')

    # # If GET request, show confirmation page (optional, but good practice)
    # # context = {
    # #     'goal': goal,
    # #     'page_title': f'Confirm Deletion: {goal.title}'
    # # }
    # return render(request, 'dashboard:dashboard_view')

# @login_required
# def time_log_view(request, goal_id):
#     """
#     Handles logging time (Creation) for a specific goal.
#     Updates the Goal's 'real_time' field atomically.
#     """
#     # Ensure the goal exists AND belongs to the logged-in user
#     goal = get_object_or_404(Goal, pk=goal_id, user=request.user)
    
#     if request.method == 'POST':
#         form = TimeLogForm(request.POST)
#         if form.is_valid():
#             minutes_logged = form.clean_duration_minutes['minutes']
#             time_to_add = timedelta(minutes=minutes_logged)
            
#             # 1. Save the TimeLog instance
#             time_log = form.save(commit=False)
#             time_log.goal = goal
#             time_log.user = request.user
#             time_log.save()
            
#             # 2. Atomically Update the Goal's total time (real_time)
#             Goal.objects.filter(pk=goal_id).update(
#                 real_time=F('real_time') + time_to_add
#             )
            
#             # 3. Check for goal completion (simple check)
#             goal.refresh_from_db()
#             if goal.real_time >= goal.target_time and not goal.completed:
#                  goal.completed = True
#                  goal.save(update_fields=['completed'])
#                  messages.success(request, f"Congratulations! Goal '{goal.title}' completed!")
#             else:
#                  messages.success(request, f"Logged {minutes_logged} minutes for '{goal.title}'. Keep it up!")

#             return redirect('dashboard:dashboard_view')
    
#     form = TimeLogForm()
#     context = {
#         'goal': goal,
#         'form': form,
#         'page_title': f'Log Time for: {goal.title}'
#     }
#     return render(request, 'dashboard/time_log_form.html', context)

@login_required
def time_log_view(request, goal_id):
    """
    Handles logging time (Creation) for a specific goal.
    Updates the Goal's 'real_time' field atomically.
    """
    goal = get_object_or_404(Goal, pk=goal_id, user=request.user)

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
                #increment = Value(timedelta(minutes=int(time_log.minutes)), output_field=DurationField())
                # increment = ExpressionWrapper(
                #     Value(time_log.minutes) * Value(60.0),  # seconds
                #     output_field=DurationField(),
                # )
                # new_value = ExpressionWrapper(
                #     Coalesce(F('real_time'), Value(timedelta(0), output_field=DurationField())) + increment,
                #     output_field=DurationField(),
                # )
                # Goal.objects.filter(pk=goal.pk).update(real_time=new_value)

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

# @login_required
# def time_log_edit_view(request, log_id):
#     """
#     Handles editing an existing TimeLog entry.
#     Requires complex logic to subtract old time and add new time to the parent Goal.
#     """
#     # Get the existing log and ensure it belongs to the user
#     log_instance = get_object_or_404(TimeLog, pk=log_id, user=request.user)
#     goal = log_instance.goal # Parent Goal
    
#     if request.method == 'POST':
#         form = TimeLogForm(request.POST, instance=log_instance)
#         if form.is_valid():
#             # Old time logged, before form save
#             minutes_old = log_instance.minutes
#             minutes_new = form.cleaned_data['minutes']
            
#             # Calculate the difference in time to adjust the Goal total
#             minutes_delta = minutes_new - minutes_old
#             time_delta = timedelta(minutes=minutes_delta)

#             with transaction.atomic():
#                 # 1. Update the Goal's total time atomically
#                 Goal.objects.filter(pk=goal.id).update(
#                     real_time=F('real_time') + time_delta
#                 )
                
#                 # 2. Save the updated TimeLog instance
#                 form.save()

#                 # 3. Re-check for goal completion
#                 goal.refresh_from_db()
#                 if goal.real_time >= goal.target_time and not goal.completed:
#                     goal.completed = True
#                     goal.save(update_fields=['completed'])
#                     messages.success(request, f"Goal '{goal.title}' completed after log update!")

#                 messages.success(request, f"Time log updated from {minutes_old}m to {minutes_new}m.")
#                 return redirect('dashboard:dashboard_view')
#     else:
#         form = TimeLogForm(instance=log_instance)
    
#     context = {
#         'form': form,
#         'goal': goal,
#         'page_title': f'Edit Log: {log_instance}'
#     }
#     return render(request, 'dashboard/time_log_form.html', context)

# @login_required
# @require_POST
# @transaction.atomic # Ensure Goal update and Log deletion happen together
# def time_log_delete_view(request, log_id):
#     """
#     Handles deletion of a TimeLog entry via an AJAX request.
#     Atomically subtracts time from the parent Goal and returns JSON.
#     """
#     try:
#         # 3. Get the log and ensure it belongs to the user
#         log_instance = get_object_or_404(TimeLog, pk=log_id, user=request.user)
#         goal = log_instance.goal
#         minutes_to_subtract = log_instance.minutes
#         time_to_subtract = timedelta(minutes=minutes_to_subtract)

#         # 4. Atomically subtract the time from the Goal's total
#         Goal.objects.filter(pk=goal.id).update(
#             real_time=F('real_time') - time_to_subtract
#         )
        
#         # 5. Delete the TimeLog
#         log_instance.delete()
        
#         # 6. Check/update completed status
#         goal.refresh_from_db()
#         goal_is_now_incomplete = False
#         if goal.completed and goal.real_time < goal.target_time:
#             goal.completed = False
#             goal.save(update_fields=['completed'])
#             goal_is_now_incomplete = True

#         # 7. Return a JSON response instead of redirecting
#         return JsonResponse({
#             'status': 'success',
#             'message': f"Log of {minutes_to_subtract} minutes deleted.",
#             'goal_was_affected': goal_is_now_incomplete,
#         })

#     except TimeLog.DoesNotExist:
#         return JsonResponse({'status': 'error', 'message': 'Log not found.'}, status=404)
#     except Exception as e:
#         return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
# @login_required
# def goal_reflection_fragment_view(request, goal_id): # Renamed function
#     """
#     Returns only the HTML fragment (content) needed for the reflection modal.
#     """
#     # Ensure the goal exists AND belongs to the logged-in user
#     goal = get_object_or_404(Goal, pk=goal_id, user=request.user)
    
#     # Calculate progress for display
#     real_time_seconds = goal.real_time.total_seconds()
#     target_time_seconds = goal.target_time.total_seconds()
    
#     progress_percentage = 0
#     if target_time_seconds > 0:
#         progress_percentage = round((real_time_seconds / target_time_seconds) * 100, 2)
        
#     time_logs = TimeLog.objects.filter(
#         user=request.user, 
#         goal=goal
#     ).order_by('-log_date', '-minutes') 
    
#     context = {
#         'goal': goal,
#         'progress_percentage': progress_percentage,
#         'time_logs': time_logs,
#     }
    
#     # Render only the fragment template
#     return render(request, 'dashboard/reflection_fragment.html', context)

# ... your other views (dashboard, goal_create, etc.) ...

@login_required
def goal_reflection_fragment(request, goal_id):
    """
    Fetches and renders an HTML fragment for the reflection modal.
    This view is called via JavaScript (Fetch API).
    """
    # 1. Get the goal, ensuring it belongs to the logged-in user for security.
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    
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