from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction # Important for ensuring both save operations succeed
from .forms import TeamForm, TeamGoalForm
from .models import TeamMember
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
    Handles the creation of a new Team.
    The user who creates the team is automatically assigned the ADMIN role.
    """
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            
            # Use a transaction to ensure both the Team and TeamMember records
            # are created successfully, or neither are created.
            try:
                with transaction.atomic():
                    # 1. Save the Team instance
                    team = form.save()
                    
                    # 2. Create the TeamMember entry for the creator
                    # Assign the creator the ADMIN role
                    TeamMember.objects.create(
                        user=request.user,
                        team=team,
                        role=TeamMember.Role.ADMIN
                    )
                
                messages.success(request, f"Team '{team.team_name}' created successfully. You are the team admin!")
                
                # Redirect to the team's detail page (we will assume its URL name is 'team_detail')
                return redirect('teams:team_detail', team_id=team.id)

            except Exception as e:
                messages.error(request, f"Error creating team: {e}")
                
        else:
            messages.error(request, "Please correct the errors below.")
            
    else:
        # GET request: show a blank form
        form = TeamForm()
    
    context = {
        'form': form,
        'page_title': 'Start a New Team'
    }
    return render(request, 'teams/team_form.html', context)

# Placeholder for the team list view
@login_required
def team_list_view(request):
    # Fetch all teams the user is a member of
    user_teams = request.user.teams.all() 
    context = {'user_teams': user_teams}
    return render(request, 'teams/team_list.html', context)
    
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
    
    if request.method == 'POST':
        form = TeamGoalForm(request.POST)
        if form.is_valid():
            # 2. Save the goal instance, but don't commit yet
            team_goal = form.save(commit=False)
            
            # 3. Assign the target team
            team_goal.team = team
            
            # 4. Save the instance
            team_goal.save()
            
            messages.success(request, f"Team Goal '{team_goal.title}' created successfully for {team.team_name}!")
            
            # Redirect back to the team's detail page
            return redirect('teams:team_detail', team_id=team.id)
        else:
            messages.error(request, "Please correct the errors below.")
            
    else:
        # GET request: show a blank form
        form = TeamGoalForm()
    
    context = {
        'form': form,
        'team': team,
        'page_title': f'Create New Team Goal for {team.team_name}'
    }
    # We will use the same form template as the personal goals, but perhaps in the teams folder
    return render(request, 'teams/team_goal_form.html', context)

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