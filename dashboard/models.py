from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta

# Abastract base goal model
class BaseGoal(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # We use null=True here because PersonalGoal allows it
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True) 
    
    target_time = models.DurationField(
        help_text="Target time to spend"
    )
    real_time = models.DurationField(
        default=timedelta(seconds=0),
        help_text="Actual time spent so far"
    )
    
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # We use auto_now=True as it's more common
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        abstract = True # This makes it a template, not a database table
        ordering = ['-created_at']

    @property
    def target_minutes(self):
        """Converts the target_time DurationField into total minutes."""
        if self.target_time:
            return int(self.target_time.total_seconds() / 60)
        return 0
        
class PersonalGoal(BaseGoal):
    """
    Represents a user-created personal goal.
    Inherits all common fields from BaseGoal.
    """
    # Unique fields for PersonalGoal
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='goals'
    )
    days_of_the_week = models.CharField(max_length=7, blank=True) 
    importance_level = models.PositiveSmallIntegerField(
        default=1,
        validators = [MinValueValidator(1), MaxValueValidator(5)]) 

    class Meta:
        db_table = 'dashboard_goal'

    def __str__(self):
        return f"Personal Goal: {self.title} ({self.user.username})"

# Abstract Base Time Log Model
class BaseTimeLog(models.Model):
    # These fields are common to both models
    log_date = models.DateField(default=timezone.now)
    minutes = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Time spent in minutes for this log"
    )
    notes = models.TextField(blank=True, null=True, help_text="Optional notes for this log")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True # This makes it a template
        ordering = ['-log_date', '-created_at']

class PersonalTimeLog(BaseTimeLog):
    """
    Represents a single log of time spent on a personal goal.
    Inherits from BaseTimeLog
    """
    goal = models.ForeignKey(
        PersonalGoal, 
        on_delete=models.CASCADE, 
        related_name='time_logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='personal_time_log'
    )
    class Meta:
        db_table = 'dashboard_timelog' # Assumes 'dashboard' is your app name

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
        PersonalGoal, # Your personal Goal model
        on_delete=models.CASCADE,
        related_name='tasks'
    )