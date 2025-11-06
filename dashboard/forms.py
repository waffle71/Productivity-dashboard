# In dashboard/forms.py (New File)

from django import forms
from .models import Goal, TimeLog
from datetime import timedelta

class GoalForm(forms.ModelForm):
    # Overriding the target_time field for better user input experience
    # Since DurationField can be complex to input, we will take hours/minutes
    # and convert it to a DurationField in the clean method.
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
        model = Goal
        # Exclude fields that are set automatically or should not be user-editable on creation
        exclude = ('user', 'real_time', 'completed')
        # We will manually handle 'target_time' using our custom fields
        
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'days_of_the_week': forms.TextInput(attrs={'placeholder': 'e.g., 1111100 for Mon-Fri'}),
        }
    
    # Custom cleaning method to combine hours/minutes into the DurationField (target_time)
    def clean(self):
        cleaned_data = super().clean()
        
        # Get custom fields
        hours = cleaned_data.get('target_hours', 0)
        minutes = cleaned_data.get('target_minutes', 0)
        
        # Calculate total duration
        total_duration = timedelta(hours=hours, minutes=minutes)

        if total_duration == timedelta(seconds=0):
            # Enforce that the user sets a target time
            raise forms.ValidationError("You must set a target time (hours or minutes) for your goal.")

        # Assign the calculated duration back to the model's 'target_time' field
        cleaned_data['target_time'] = total_duration
        
        # Remove the temporary fields so they don't interfere with model saving
        del cleaned_data['target_hours']
        del cleaned_data['target_minutes']
        
        return cleaned_data
    
class TimeLogForm(forms.ModelForm):
    """
    A simple form for users to log time spent in minutes on a specific goal.
    """
    class Meta:
        model = TimeLog
        # Only prompt for the number of minutes
        fields = ('minutes',) 
        
        widgets = {
            'minutes': forms.NumberInput(attrs={
                'min': 1, 
                'placeholder': 'Minutes spent',
                'required': True
            }),
        }