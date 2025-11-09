from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from .models import TeamMember, TeamGoalComment
from users.models import Notification

@receiver(post_save, sender=TeamMember)
def send_notification_on_join(sender, instance, created, **kwargs):
    """
    When a new TeamMember is created, send a notification
    to all admins of that team.
    """
    
    # 2. ADD A PRINT STATEMENT FOR DEBUGGING
    # This will show up in your 'runserver' console
    print(f"--- TeamMember save signal fired! Created: {created} ---")

    new_member_instance = instance
    
    # 3. USE THE CORRECT CLASS ATTRIBUTE
    # Use 'TeamMember.Role.MEMBER', not 'TeamMember.Role'
    if created and new_member_instance.role == TeamMember.Role.MEMBER:
        
        print(f"--- New member {new_member_instance.user.username} joined. Notifying admins... ---")
        
        team = new_member_instance.team
        new_user = new_member_instance.user
        
        # Find all admins
        admins = TeamMember.objects.filter(
            team=team, 
            role=TeamMember.Role.ADMIN
        )
        
        message_body = (
            f"'{new_user.username}' has joined your team: '{team.team_name}'."
        )
        notification_link = reverse(
            'teams:team_dashboard', 
            args=[team.id]
        )

        for admin_member in admins:
            # 4. LOGIC IMPROVEMENT
            # Don't notify the new user if they somehow joined as an admin
            if admin_member.user != new_user:
                Notification.objects.create(
                    user=admin_member.user,
                    message=message_body,
                    link=notification_link
                )
                print(f"--- Sent notification to {admin_member.user.username} ---")