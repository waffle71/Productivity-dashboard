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
    # 'instance' is the new TeamMember object that was saved
    new_member_instance = instance
    
    # We only care about NEWLY created memberships,
    # AND only when a new 'MEMBER' joins (not the admin creating the team).
    if created and new_member_instance.role == TeamMember.Role.MEMBER:
        
        team = new_member_instance.team
        new_user = new_member_instance.user
        
        # 1. Find all admins for this team
        admins = TeamMember.objects.filter(
            team=team, 
            role=TeamMember.Role.ADMIN
        )
        
        # 2. Create the message and link
        message_body = (
            f"'{new_user.username}' has joined your team: '{team.team_name}'."
        )
        notification_link = reverse(
            'teams:team_dashboard', 
            args=[team.id]
        )

        # 3. Create a notification for each admin
        for admin_member in admins:
            # Admins don't need to be notified that a new member joined
            # if they were the one who added them (this is a good check)
            # But for a simple "join" button, this is fine.
            Notification.objects.create(
                user=admin_member.user,
                message=message_body,
                link=notification_link
            )