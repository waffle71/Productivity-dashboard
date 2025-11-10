from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
class Goal(models.Model):
    """
    Represents a user-created personal goal.
    Based on the 'Goal' schema 
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
    
    # Time fields 
    target_time = models.DurationField(
        help_text="Target time to spend (e.g., '10:00:00' for 10 hours)"
    )
    real_time = models.DurationField(
        default=timedelta(seconds=0),
        help_text="Actual time spent so far"
    )
        
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    # Stored as a string like '1111100' (Mon-Fri) 
    days_of_the_week = models.CharField(max_length=7, blank=True) 
    
    # Importance level from 1-5 
    importance_level = models.PositiveSmallIntegerField(
        default=1,
        validators = [MinValueValidator(1), MaxValueValidator(5)]) 

    def __str__(self):
        return f"{self.title} ({self.user.username})"

class TimeLog(models.Model):
    """
    Represents a single log of time spent on a personal goal.
    Based on the 'TimeLog' schema 
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
    log_date = models.DateField()
    minutes = models.IntegerField(help_text="Time spent in minutes for this log")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.minutes} minutes for {self.goal.title} on {self.log_date}"

# Abstract base class for tasks
class BaseTask(models.Model):
    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True # This model won't exist in the database
        ordering = ['completed', 'created_at']

    def __str__(self):
        return self.title
    
# Concrete model representing a task associated with a specific goal.   
class Task(BaseTask):
    """
    Represents a single to-do item for a user's personal Goal.
    Inherits common fields and behavior from BaseTask.
    """
    # Foreign key linking this task to a Goal instance
    goal = models.ForeignKey(
        Goal, # Your personal Goal model
        on_delete=models.CASCADE,
        related_name='tasks'
    )