from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import CustomUser

BASE_INPUT = (
    "mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 "
    "text-gray-900 placeholder-gray-400 focus:outline-none "
    "focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
)

class CustomUserCreationForm(UserCreationForm):
    """
    A form for creating new users. Includes all required fields
    and the 'role' field.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": BASE_INPUT,
            "placeholder": "you@example.com",
            "autocomplete": "email",
        })
    )
    
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Add 'email' and 'role' to the fields
        fields = ('username', 'email', 'role')
        widgets = {
            "username": forms.TextInput(attrs={
                "class": BASE_INPUT,
                "placeholder": "yourname",
                "autocomplete": "username",
            }),
            # If role is a ChoiceField on the model, Select works great:
            "role": forms.Select(attrs={
                "class": "mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 "
                         "text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 "
                         "focus:border-blue-500",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Tailwind classes to password1/password2 (they aren't in Meta)
        self.fields["password1"].widget.attrs.update({
            "class": BASE_INPUT,
            "placeholder": "••••••••",
            "autocomplete": "new-password",
        })
        self.fields["password2"].widget.attrs.update({
            "class": BASE_INPUT,
            "placeholder": "confirm password",
            "autocomplete": "new-password",
        })
        # Optional: shorter help texts
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""

class CustomUserChangeForm(UserChangeForm):
    """
    A form for updating user information (like in the admin panel).
    """
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'role')

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 "
                     "text-gray-900 placeholder-gray-400 focus:outline-none "
                     "focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
            "placeholder": "yourname",
            "autocomplete": "username",
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 "
                     "text-gray-900 placeholder-gray-400 focus:outline-none "
                     "focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
            "placeholder": "••••••••",
            "autocomplete": "current-password",
        })
    )


