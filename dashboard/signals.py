from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import F
from datetime import timedelta 
from .models import TimeLog, Goal

# Receiver function that listens for the post_save signal from the TimeLog model
@receiver(post_save, sender=TimeLog)
def update_goal_and_streak(sender, instance, created, **kwargs):
    """
    Observer/Receiver function triggered after a TimeLog is saved.
    Updates the Goal's total time and potentially a User's streak.

    
    Parameters:
    - sender: The model class (TimeLog)
    - instance: The actual instance of TimeLog that was saved
    - created: Boolean indicating if this was a new instance
    - kwargs: Additional keyword arguments
    """
    if created:
        # Convert the integer minutes into a timedelta object
        duration_to_add = timedelta(minutes=instance.minutes)
        
        # Observer Action 1: Increment the Goal's real_time field by the new duration
        Goal.objects.filter(pk=instance.goal_id).update(
            real_time=F('real_time') + duration_to_add
        )
        
        # Observer Action 2 (Optional): Check if the goal is now completed
        goal = Goal.objects.only('real_time', 'target_time', 'completed').get(pk=instance.goal_id)
        
        # If the goal has a target time, and the accumulated time meets or exceeds it,
        # and the goal hasn't already been marked completed, then mark it as completed
        if goal.target_time and goal.real_time >= goal.target_time and not goal.completed:
            goal.completed = True
            goal.save(update_fields=['completed'])
            