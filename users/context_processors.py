# In users/context_processors.py
from .models import Notification

def unread_notifications(request):
    """
    Makes unread notifications available to all templates.
    """
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(
            user=request.user, 
            is_read=False
        )
        return {
            'unread_notifications': notifications,
            'unread_notification_count': notifications.count()
        }
    return {}