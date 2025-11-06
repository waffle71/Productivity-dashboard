from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    A form for creating new users. Includes all required fields
    and the 'role' field.
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Add 'email' and 'role' to the fields
        fields = ('username', 'email', 'role')

class CustomUserChangeForm(UserChangeForm):
    """
    A form for updating user information (like in the admin panel).
    """
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'role')