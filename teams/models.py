from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator
from datetime import timedelta
from dashboard.models import BaseTask, BaseGoal, BaseTimeLog

class Team(models.Model):
    """
    Represents a team.
    Based on the 'Team' schema 
    """
    team_name = models.CharField(max_length=255)
    team_desc = models.TextField(blank=True, null=True, help_text="Description")
    
    # Creates a Many-to-Many relationship with CustomUser
    # through the TeamMember model
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='TeamMember',
        related_name='teams'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.team_name 

class TeamMember(models.Model):
    """
    Links a user to a team and defines their role within that team.
    Based on the 'TeamMember' schema 
    """
    class Role(models.TextChoices):
        MEMBER = 'MEMBER', 'Member'
        ADMIN = 'ADMIN', 'Admin' # Or 'Leader'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        # Ensures a user can only be on a team once
        unique_together = ('user', 'team')

    def __str__(self):
        return f"{self.user.username} - {self.team.team_name} ({self.role})"

class TeamGoal(BaseGoal):
    """
    Represents a goal associated with a specific team.
    Inherits all common fields from BaseGoal.
    """
    # Unique field for TeamGoal
    team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        related_name='team_goals'
    )
    
    class Meta:
        db_table = 'teams_teamgoal'

    def __str__(self):
        return f"Team Goal: {self.title} ({self.team.team_name})"

class TeamTimeLog(BaseTimeLog):
    """
    Represents a single log of time spent by a user on a team goal.
    Inherits from BaseTimeLog.
    """
    goal = models.ForeignKey(
        TeamGoal, 
        on_delete=models.CASCADE, 
        related_name='time_logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='team_time_logs'
    )
    class Meta:
        db_table = 'teams_teamtimelog'

    def __str__(self):
        return f"{self.user.username} logged {self.minutes}m for {self.goal.title}"
    
class TeamTask(BaseTask):
    """
    Represents a to-do item for a TeamGoal.
    Inherits from dashboard.models.BaseTask.
    """
    goal = models.ForeignKey(
        TeamGoal, 
        on_delete=models.CASCADE, 
        related_name='tasks'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_tasks'
    )

class TeamGoalComment(models.Model):
    goal = models.ForeignKey(TeamGoal, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='team_comments')
    body = models.TextField(help_text="The content of the comment")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['created_at']
    def __str__(self):
        return f"Comment by {self.user.username} on {self.goal.title}"