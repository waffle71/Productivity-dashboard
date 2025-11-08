# In teams/forms.py (New File)

from django import forms
from .models import Team, TeamGoal, TeamTimeLog
from datetime import timedelta
from django.core.exceptions import ValidationError
from .models import Team

TW_INPUT = "mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
TW_TEXTAREA = "mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"

class TeamForm(forms.ModelForm):
    team_name = forms.CharField(
        label="Team name",
        min_length=3,
        max_length=255,
        widget=forms.TextInput(attrs={
            "placeholder": "e.g., Morning Study Crew",
            "class": TW_INPUT
        }),
        help_text="Pick a short, memorable name (3+ characters).",
    )
    team_desc = forms.CharField(
        label="Description (optional)",
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "What is this team about? Who should join? Any norms or goals?",
            "class": TW_TEXTAREA
        }),
        help_text="Describe the purpose so others know what to expect.",
    )

    class Meta:
        model = Team
        fields = ["team_name", "team_desc"]

    def clean_team_name(self):
        name = (self.cleaned_data.get("team_name") or "").strip()
        if len(name) < 3:
            raise ValidationError("Team name must be at least 3 characters.")
        # Case-insensitive uniqueness check (friendly UX)
        qs = Team.objects.filter(team_name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("That name is already taken. Please choose another.")
        return name

class TeamGoalForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Define the common classes
        common_classes = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
        
        # Add *only* the CSS classes in this __init__ method
        self.fields['title'].widget.attrs.update({'class': common_classes})
        self.fields['description'].widget.attrs.update({'class': common_classes, 'rows': 3})
        self.fields['start_date'].widget.attrs.update({'class': common_classes})
        self.fields['end_date'].widget.attrs.update({'class': common_classes})
        self.fields['target_time'].widget.attrs.update({'class': common_classes})

    class Meta:
        model = TeamGoal
        fields = ['title', 'description', 'start_date', 'end_date', 'target_time']
        
        # --- THIS IS THE FIX ---
        # We define the widget type here, not in __init__
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
        # --- END OF FIX ---
        
        help_texts = {
            'target_time': 'Enter duration (e.g., "10 days", "20:00:00" for 20 hours, or "1:30:00" for 90 minutes).'
        }

class TeamTimeLogForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        common_classes = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
        
        self.fields['log_date'].widget.attrs.update({'class': common_classes})
        self.fields['minutes'].widget.attrs.update({'class': common_classes, 'type': 'number', 'min': 1})
        self.fields['notes'].widget.attrs.update({'class': common_classes, 'rows': 3})

    class Meta:
        model = TeamTimeLog
        # These are the fields the user will fill out.
        # 'user' and 'goal' will be set automatically by the view.
        fields = ['log_date', 'minutes', 'notes']
        
        widgets = {
            'log_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
        labels = {
            'log_date': 'Date of Work',
            'minutes': 'Minutes Logged',
            'notes': 'Notes (What did you do?)'
        }