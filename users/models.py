from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
# Create your models here.
class CustomUser(AbstractUser):
    """
    Extends the default User model to add roles.
    """
    
    # User roles as defined in the proposal 
    class Role(models.TextChoices):
        USER = 'USER', 'User'
        ADMIN = 'ADMIN', 'Admin'

    # The 'role' field from the 'User accounts' table 
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.USER)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.username
    
class Notification(models.Model):
    # The user who should receive the notification
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    
    # The message (e.g., "Jia left a comment...")
    message = models.TextField()
    
    # The link to go to when clicked
    link = models.CharField(max_length=255, blank=True, null=True)
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # Show newest first

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:30]}"