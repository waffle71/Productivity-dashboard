from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import F
from datetime import timedelta # <-- Import timedelta
from .models import TimeLog, Goal

@receiver(post_save, sender=TimeLog)
def update_goal_and_streak(sender, instance, created, **kwargs):
    """
    Observer/Receiver function triggered after a TimeLog is saved.
    Updates the Goal's total time and potentially a User's streak.
    """
    if created:
        # 1. Convert the integer minutes into a timedelta object
        # This is the Duration field value you want to ADD.
        duration_to_add = timedelta(minutes=instance.minutes)
        
        # Observer Action 1: Update Goal.real_time
        # Use F() to reference the current DB value, and add the timedelta object.
        # Django knows how to convert the timedelta object into a DB-appropriate duration.
        Goal.objects.filter(pk=instance.goal_id).update(
            real_time=F('real_time') + duration_to_add
        )
        
        # ... (other actions)

        # Optional Observer Action 3: Check for Completion
        # NOTE: You MUST refresh the goal from the database to see the F() update!
        # The goal object in memory (goal = Goal.objects.get(...)) 
        # will have the OLD 'real_time' value.

        #goal = Goal.objects.get(pk=instance.goal_id) 
        # OR better:
        goal = Goal.objects.only('real_time', 'target_time', 'completed').get(pk=instance.goal_id)

        # 🚨 This part is potentially where the 'unsupported type' error originated, 
        # IF you had an *existing bad data* in the DB that this query tried to load.
        # The fix above should prevent *new* bad data, but if old bad data exists, 
        # the .get() will still try to load it and fail.
        
        if goal.target_time and goal.real_time >= goal.target_time and not goal.completed:
            goal.completed = True
            goal.save(update_fields=['completed'])
            # Send another signal/notification (e.g., to the team leader)