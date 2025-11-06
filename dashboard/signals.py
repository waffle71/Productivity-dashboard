from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import F
from .models import TimeLog, Goal

@receiver(post_save, sender=TimeLog)
def update_goal_and_streak(sender, instance, created, **kwargs):
    """
    Observer/Receiver function triggered after a TimeLog is saved.
    Updates the Goal's total time and potentially a User's streak.
    """
    if created:
        time_to_add = instance.minutes # Assuming minutes is an integer
        
        # Observer Action 1: Update Goal.real_time
        # This is where your existing F-expression logic should live now.
        Goal.objects.filter(pk=instance.goal_id).update(
            real_time=F('real_time') + time_to_add
        )
        
        # Observer Action 2: Update User Streak (Hypothetical Service)
        # streak_service.update_streak(instance.user) 
        
        # Optional Observer Action 3: Check for Completion
        goal = Goal.objects.get(pk=instance.goal_id)
        if goal.real_time >= goal.target_time and not goal.completed:
            goal.completed = True
            goal.save(update_fields=['completed'])
            # Send another signal/notification (e.g., to the team leader)