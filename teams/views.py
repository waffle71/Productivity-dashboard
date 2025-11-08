from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError # Important for ensuring both save operations succeed
from django.db.models import Q, Count, Exists, OuterRef, Sum
from django.db.models.functions import Coalesce
from .forms import TeamForm, TeamGoalForm, TeamTimeLogForm
from .models import TeamMember, Team, TeamGoal, TeamTimeLog
from dashboard.models import Goal
from users.decorators import admin_required
from users.models import CustomUser

@admin_required
def admin_dashboard_view(request):
    """
    The main administration dashboard, accessible only to users with the 'ADMIN' role.
    This is where they can 'Generate templates, create and push challenges'.
    """
    
    # In a real application, you would fetch data relevant to administration here:
    # 1. Total number of users, teams, and goals.
    # 2. List of current challenges.
    # 3. Forms to create new challenges or templates.
    
    # Placeholder context
    context = {
        'page_title': 'Admin Control Panel',
        'admin_tasks': [
            {'name': 'Create Motivational Challenge', 'url': '#'}, # Will link to a future view
            {'name': 'Generate Template/Report', 'url': '#'},
            {'name': 'Manage All Users', 'url': 'teams:user_management'},
        ]
    }
    
    return render(request, 'teams/admin_dashboard.html', context)

@login_required
def team_create_view(request):
    """
    Creates a new Team and assigns the creator as ADMIN.
    """
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    team = form.save()  # team_name & team_desc already cleaned
                    TeamMember.objects.create(
                        user=request.user,
                        team=team,
                        role=TeamMember.Role.ADMIN
                    )
                messages.success(request, f"🎉 Team “{team.team_name}” created! You’re the admin.")
                return redirect('teams:team_dashboard', team_id=team.id)
            except IntegrityError:
                messages.error(request, "A team with that name already exists. Please try another.")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = TeamForm()

    return render(request, 'teams/team_form.html', {
        'form': form,
        'page_title': 'Create a New Team'
    })
    
# Placeholder for the team detail view (needed for the redirect above)
@login_required
def team_detail_view(request, team_id):
    # Retrieve the team and ensure the user is a member
    team = get_object_or_404(request.user.teams, pk=team_id)
    # You would pass team goals, member list, etc., here.
    context = {'team': team}
    return render(request, 'teams/team_detail.html', context)

@login_required
def team_goal_create_view(request, team_id):
    """
    Handles the creation of a new TeamGoal linked to a specific team.
    Only allows creation if the user is a member of the team.
    """
    # 1. Check if the team exists AND the user is a member of it.
    team = get_object_or_404(request.user.teams, pk=team_id)

    try:
        member_instance = TeamMember.objects.get(user=request.user, team=team)
        if member_instance.role != TeamMember.Role.ADMIN:
            messages.error(request, "You must be a team admin to create new goals.")
            return redirect('teams:team_dashboard', team_id=team.id)
            
    except TeamMember.DoesNotExist:
        messages.error(request, "You are not a member of this team.")
        return redirect('dashboard:dashboard_view') # Redirect to main dashboard
    
    if request.method == 'POST':
        form = TeamGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.team = team  # Assign the team from the URL
            goal.save()
            messages.success(request, f"New goal '{goal.title}' has been created!")
            return redirect('teams:team_dashboard', team_id=team.id)
        else:
            messages.error(request, "Please correct the errors below.")
            
    else: # GET Request
        form = TeamGoalForm()

    context = {
        'page_title': 'Create New Goal',
        'form': form,
        'team': team
    }
    return render(request, 'teams/team_goal_form.html', context)

@login_required
def team_goal_edit_view(request, team_id, goal_id):
    """
    Handles editing an existing team goal.
    Only Team Admins can access this.
    """
    team = get_object_or_404(Team, pk=team_id)
    goal = get_object_or_404(TeamGoal, pk=goal_id, team=team) # Ensure goal belongs to team

    # --- Security Check: User must be an Admin ---
    try:
        member_instance = TeamMember.objects.get(user=request.user, team=team)
        if member_instance.role != TeamMember.Role.ADMIN:
            messages.error(request, "You must be a team admin to edit goals.")
            return redirect('teams:team_dashboard', team_id=team.id)
    except TeamMember.DoesNotExist:
        messages.error(request, "You are not a member of this team.")
        return redirect('dashboard:dashboard_view') # Or your main dashboard
    # --- End Security Check ---

    if request.method == 'POST':
        # Populate the form with POST data AND the existing goal instance
        form = TeamGoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, f"Goal '{goal.title}' has been updated.")
            return redirect('teams:team_dashboard', team_id=team.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # GET request: Populate the form with the goal's current data
        form = TeamGoalForm(instance=goal)

    context = {
        'page_title': f'Edit Goal: {goal.title}',
        'form': form,
        'team': team,
        'goal': goal
    }
    # We reuse the same template as the create view!
    return render(request, 'teams/team_goal_form.html', context)


@login_required
def team_goal_delete_view(request, team_id, goal_id):
    """
    Handles deleting a team goal after confirmation.
    Only Team Admins can access this.
    """
    team = get_object_or_404(Team, pk=team_id)
    goal = get_object_or_404(TeamGoal, pk=goal_id, team=team)

    # --- Security Check (Same as Update View) ---
    try:
        member_instance = TeamMember.objects.get(user=request.user, team=team)
        if member_instance.role != TeamMember.Role.ADMIN:
            messages.error(request, "You must be a team admin to delete goals.")
            return redirect('teams:team_dashboard', team_id=team.id)
    except TeamMember.DoesNotExist:
        messages.error(request, "You are not a member of this team.")
        return redirect('dashboard:dashboard_view')
    # --- End Security Check ---

    if request.method == 'POST':
        # User has confirmed deletion
        goal_title = goal.title
        goal.delete()
        messages.success(request, f"The goal '{goal_title}' has been deleted.")
        return redirect('teams:team_dashboard', team_id=team.id)
    
    # GET request: Show the confirmation page
    context = {
        'page_title': 'Confirm Deletion',
        'team': team,
        'goal': goal
    }
    return render(request, 'teams/team_goal_confirm_delete.html', context)


@admin_required
def user_management_view(request):
    """
    Displays a list of all non-Admin users for management purposes.
    Only accessible by users with the 'ADMIN' role.
    """
    
    # Fetch all users, excluding the current Admin user and potentially other Admins
    # We filter by role != 'ADMIN' to focus on the regular user base
    all_users = CustomUser.objects.filter(role=CustomUser.Role.USER).order_by('username')
    
    context = {
        'page_title': 'User Management',
        'all_users': all_users,
        'total_user_count': all_users.count()
    }
    
    return render(request, 'teams/user_management.html', context)

@login_required
def team_member_tasks_view(request, team_id):
    """
    Displays active goals for all 'MEMBER's within a specific team.
    Only accessible by 'ADMIN's of that team.
    """
    
    # 1. Verify Team Existence
    team = get_object_or_404(Team, pk=team_id)
    
    # 2. Authorization Check: Is the current user an ADMIN of this team?
    try:
        current_member_role = TeamMember.objects.get(
            user=request.user, 
            team=team
        ).role
        
        # If the user is NOT a Team Admin, redirect or raise 403
        if current_member_role != TeamMember.Role.ADMIN:
            messages.error(request, "You must be an Admin of this team to view member tasks.")
            return redirect('teams:team_dashboard', team_id=team_id) 

    except TeamMember.DoesNotExist:
        # If the user is not a member of the team at all
        messages.error(request, "You are not a member of this team.")
        return redirect('dashboard:dashboard_view') 
    
    # 3. Get Members and their Goals
    # Find all users who are simple 'MEMBER's in this team
    member_users = TeamMember.objects.filter(
        team=team, 
        role=TeamMember.Role.MEMBER
    ).values_list('user_id', flat=True)
    
    # Fetch all active goals for those members
    member_goals = Goal.objects.filter(
        user_id__in=member_users,
        completed=False 
    ).select_related('user').order_by('user__username', 'end_date')
    
    context = {
        'page_title': f'Active Tasks for Members of {team.team_name}',
        'team': team,
        'member_goals': member_goals,
        'total_member_goals': member_goals.count()
    }
    
    return render(request, 'teams/team_member_tasks.html', context)

# In teams/views.py (Modify the existing team_dashboard_view)


@login_required
def team_dashboard_view(request, team_id):
    """
    Displays the main dashboard for a specific team.
    """
    team = get_object_or_404(Team, pk=team_id)
    
    # --- START: Role Check Logic ---
    current_user_role = TeamMember.Role.MEMBER # Default to Member
    
    try:
        # Fetch the TeamMember object for the current user and team
        member_instance = TeamMember.objects.get(
            user=request.user, 
            team=team
        )
        current_user_role = member_instance.role # Set the actual role (MEMBER or ADMIN)
        
    except TeamMember.DoesNotExist:
        # Handle case where user is not a member of the team (optional: redirect or show error)
        messages.error(request, "You are not an active member of this team.")
        return redirect('dashboard:dashboard_view') 
    # --- END: Role Check Logic ---

    # Example: Fetch other team data here (members list, team goals, etc.)
    # 1. Get Team Members
    team_members = TeamMember.objects.filter(team=team).select_related('user')

    # 2. Get Team Goals with Progress
    team_goals_query = TeamGoal.objects.filter(team=team).annotate(
        logged_minutes=Coalesce(Sum('time_logs__minutes'), 0)
    ).order_by('end_date')

    team_goals_with_progress = []
    for goal in team_goals_query:
        percentage = 0
        # Use the target_minutes property from the model
        target = goal.target_minutes 
        logged = goal.logged_minutes
        
        if target > 0:
            percentage = (logged / target) * 100
            
        team_goals_with_progress.append({
            'goal': goal,
            'logged_minutes': logged,
            'target_minutes': target,
            'percentage': percentage,
        })

    # 3. Get Member Contributions (Time Logs)
    member_contributions = TeamTimeLog.objects.filter(
        goal__team=team
    ).values(
        'user__username'  # Group by username
    ).annotate(
        total_minutes=Sum('minutes')
    ).order_by(
        '-total_minutes'  # Show top contributors first
    )

    context = {
        'page_title': team.team_name,
        'team': team,
        'current_user_role': current_user_role, 
        
        'team_members': team_members, # From your existing code
        
        # Pass the new list to the template
        'team_goals_list': team_goals_with_progress, 
        
        'member_contributions': member_contributions,
    }
    return render(request, 'teams/team_dashboard.html', context)


@login_required
def team_list_view(request):
    """
    Explore teams. Search, filter (All/My/Joinable), and paginate.
    Annotates each team with:
      - member_count
      - is_member (for the current user)
    """
    q = (request.GET.get("q") or "").strip()
    filt = request.GET.get("filter", "all")  # all | mine | joinable
    per_page = int(request.GET.get("per_page") or 12)

    is_member_subq = TeamMember.objects.filter(
        team=OuterRef('pk'),
        user=request.user
    )

    teams = (
        Team.objects
        .annotate(
            member_count=Count('members', distinct=True),
            is_member=Exists(is_member_subq)
        )
        .order_by('team_name')
    )

    if q:
        teams = teams.filter(
            Q(team_name__icontains=q) | Q(team_desc__icontains=q)
        )

    if filt == "mine":
        teams = teams.filter(is_member=True)
    elif filt == "joinable":
        teams = teams.filter(is_member=False)

    paginator = Paginator(teams, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_title": "Explore and Manage Teams",
        "page_obj": page_obj,
        "q": q,
        "filter": filt,
        "per_page_options": [12, 24, 48],
    }
    return render(request, "teams/team_list.html", context)

# @login_required
# def team_list_view(request):
#     """
#     Displays a list of all teams the user can join.
#     """
#     # # 1. Get IDs of all teams the user is currently a member of
#     # member_of_teams_ids = TeamMember.objects.filter(
#     #     user=request.user
#     # ).values_list('team_id', flat=True)

#     # # 2. Fetch all teams that the user is NOT a member of
#     # joinable_teams = Team.objects.exclude(
#     #     id__in=member_of_teams_ids
#     # ).order_by('team_name')

#     # context = {
#     #     'page_title': 'Join an Existing Team',
#     #     'joinable_teams': joinable_teams
#     # }
#     # 1. Fetch all teams
#     all_teams = Team.objects.all().order_by('team_name')

#     # 2. Get a quick lookup of teams the user is already a member of
#     # This creates a set of team IDs for fast checking in the template/loop
#     member_of_team_ids = set(
#         TeamMember.objects.filter(user=request.user)
#         .values_list('team_id', flat=True)
#     )

#     # 3. Create a list combining team data with membership status
#     team_data = []
#     for team in all_teams:
#         is_member = team.id in member_of_team_ids
#         team_data.append({
#             'team': team,
#             'is_member': is_member
#         })

#     context = {
#         'page_title': 'Explore and Manage Teams',
#         'all_team_data': team_data, # Renamed variable for clarity
#     }
#     return render(request, 'teams/team_list.html', context)

@login_required
def team_join_view(request, team_id):
    """
    Creates a TeamMember record for the current user and the specified team.
    """
    team = get_object_or_404(Team, pk=team_id)

    # Prevent joining a team twice (crucial integrity check)
    if TeamMember.objects.filter(user=request.user, team=team).exists():
        messages.warning(request, f"You are already a member of {team.team_name}.")
        return redirect('teams:team_dashboard', team_id=team.id)

    try:
        # --- THIS IS THE CRITICAL STEP ---
        TeamMember.objects.create(
            user=request.user,
            team=team,
            role=TeamMember.Role.MEMBER # Automatically assign as a regular Member
        )
        # ---------------------------------
        
        messages.success(request, f"You have successfully joined the team: {team.team_name}!")
        return redirect('teams:team_dashboard', team_id=team.id)

    except Exception as e:
        messages.error(request, f"Failed to join team: {e}")
        return redirect('teams:team_list')
    
@login_required
def team_time_log_create_view(request, team_id, goal_id):
    """
    Handles logging time for a specific team goal.
    User must be a member of the team.
    """
    team = get_object_or_404(Team, pk=team_id)
    goal = get_object_or_404(TeamGoal, pk=goal_id, team=team) # Ensure goal belongs to team

    # --- Security Check: User must be a Member ---
    if not TeamMember.objects.filter(user=request.user, team=team).exists():
        messages.error(request, "You are not a member of this team.")
        return redirect('dashboard:dashboard_view') # Or your main dashboard
    # --- End Security Check ---

    if request.method == 'POST':
        form = TeamTimeLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user  # Set the user
            log.goal = goal          # Set the goal
            log.save()
            
            # This is important! Your dashboard view already calculates the sum
            # of logs, but if you have a 'real_time' field on the goal,
            # you would update it here.
            # E.g.:
            # goal.real_time += timedelta(minutes=log.minutes)
            # goal.save()
            
            messages.success(request, f"Successfully logged {log.minutes} minutes for '{goal.title}'.")
            return redirect('teams:team_dashboard', team_id=team.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # GET request
        form = TeamTimeLogForm()

    context = {
        'page_title': f'Log Time for: {goal.title}',
        'form': form,
        'team': team,
        'goal': goal
    }
    return render(request, 'teams/team_time_log_form.html', context)