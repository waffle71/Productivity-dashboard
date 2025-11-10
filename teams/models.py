from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator
from datetime import timedelta
from dashboard.models import BaseTask
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

class TeamGoal(models.Model):
    """
    Represents a goal associated with a specific team.
    Based on the 'TeamGoal' schema 
    """
    team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        related_name='team_goals'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    
    target_time = models.DurationField(
        help_text="Target time for the whole team"
    )
    real_time = models.DurationField(
        default=timedelta(seconds=0),
        help_text="Actual time spent by the team"
    )
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def target_minutes(self):
        """Converts the target_time DurationField into total minutes."""
        if self.target_time:
            # total_seconds() is the reliable way to get duration
            return int(self.target_time.total_seconds() / 60)
        return 0
    
    def __str__(self):
        return f"Team Goal: {self.title} ({self.team.team_name})"

class TeamTimeLog(models.Model):
    """
    Represents a single log of time spent by a user on a team goal.
    Based on the 'TeamTimeLog' schema 
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
    created_at = models.DateTimeField(auto_now_add=True)
    log_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about this time log")
    minutes = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Time spent in minutes for this log"
    )

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