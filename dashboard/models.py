from django.db import models
from django.conf import settings
from datetime import timedelta

# Create your models here.

class Goal(models.Model):
    """
    Represents a user-created personal goal.
    Based on the 'User created goals' schema [cite: 68]
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='goals'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    
    # Time fields [cite: 68]
    target_time = models.DurationField(
        help_text="Target time to spend (e.g., '10:00:00' for 10 hours)"
    )
    real_time = models.DurationField(
        default=timedelta(seconds=0),
        help_text="Actual time spent so far"
    )
        
    completed = models.BooleanField(default=False)
    
    # Stored as a string like '1111100' (Mon-Fri) [cite: 68]
    days_of_the_week = models.CharField(max_length=7, blank=True) 
    
    # Importance level from 1-5 [cite: 68]
    importance_level = models.IntegerField(default=1) 

    def __str__(self):
        return f"{self.title} ({self.user.username})"

class TimeLog(models.Model):
    """
    Represents a single log of time spent on a personal goal.
    Based on the 'Time_log' schema [cite: 69, 70]
    """
    goal = models.ForeignKey(
        Goal, 
        on_delete=models.CASCADE, 
        related_name='time_logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='time_logs'
    )
    log_date = models.DateField(auto_now_add=True)
    minutes = models.IntegerField(help_text="Time spent in minutes for this log")

    def __str__(self):
        return f"{self.minutes} minutes for {self.goal.title} on {self.log_date}"