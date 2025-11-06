from django.contrib.auth.models import AbstractUser
from django.db import models

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