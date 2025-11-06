# In teams/forms.py (New File)

from django import forms
from .models import Team, TeamGoal
from datetime import timedelta

class TeamForm(forms.ModelForm):
    """
    Form for creating a new Team.
    """
    class Meta:
        model = Team
        fields = ('team_name', 'desc')
        labels = {
            'team_name': 'Team Name',
            'desc': 'Description (Optional)',
        }

class TeamGoalForm(forms.ModelForm):
    """
    Form for creating a new TeamGoal.
    Includes custom fields for target time input.
    """
    target_hours = forms.IntegerField(
        min_value=0, 
        initial=0, 
        label="Target Hours",
        required=False
    )
    target_minutes = forms.IntegerField(
        min_value=0, 
        max_value=59, 
        initial=0, 
        label="Target Minutes",
        required=False
    )

    class Meta:
        model = TeamGoal
        # Exclude 'team', 'real_time', and 'completed' as they are set programmatically
        exclude = ('team', 'real_time', 'completed') 
        
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        
        # Get custom fields
        hours = cleaned_data.get('target_hours', 0)
        minutes = cleaned_data.get('target_minutes', 0)
        
        # Calculate total duration
        total_duration = timedelta(hours=hours, minutes=minutes)

        if total_duration == timedelta(seconds=0):
            raise forms.ValidationError("You must set a target time (hours or minutes) for your team goal.")

        # Assign the calculated duration back to the model's 'target_time' field
        cleaned_data['target_time'] = total_duration
        
        # Remove the temporary fields
        del cleaned_data['target_hours']
        del cleaned_data['target_minutes']
        
        return cleaned_data