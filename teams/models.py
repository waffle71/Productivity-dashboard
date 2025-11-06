from django.db import models
from django.conf import settings
from datetime import timedelta

# Create your models here.
class Team(models.Model):
    """
    Represents a team.
    Based on the 'Teams' schema [cite: 60, 61]
    """
    team_name = models.CharField(max_length=255)
    desc = models.TextField(blank=True, null=True, help_text="Description")
    
    # Creates a Many-to-Many relationship with CustomUser
    # through the TeamMember model
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='TeamMember',
        related_name='teams'
    )

    def __str__(self):
        return self.team_name

class TeamMember(models.Model):
    """
    Links a user to a team and defines their role within that team.
    This is the 'Team_members' table [cite: 63, 64]
    """
    class Role(models.TextChoices):
        MEMBER = 'MEMBER', 'Member'
        ADMIN = 'ADMIN', 'Admin' # Or 'Leader'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.MEMBER)

    class Meta:
        # Ensures a user can only be on a team once
        unique_together = ('user', 'team')

    def __str__(self):
        return f"{self.user.username} - {self.team.team_name} ({self.role})"

class TeamGoal(models.Model):
    """
    Represents a goal associated with a specific team.
    Based on the 'Team goals' schema [cite: 71, 72, 73]
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

    def __str__(self):
        return f"Team Goal: {self.title} ({self.team.team_name})"

class TeamTimeLog(models.Model):
    """
    Represents a single log of time spent by a user on a team goal.
    Based on the 'team_Time_log' schema [cite: 75, 76]
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
    log_date = models.DateField(auto_now_add=True)
    minutes = models.IntegerField(help_text="Time spent in minutes for this log")

    def __str__(self):
        return f"{self.user.username} logged {self.minutes}m for {self.goal.title}"