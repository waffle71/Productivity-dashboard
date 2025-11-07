# In dashboard/forms.py (New File)

from django import forms
from .models import Goal, TimeLog
from datetime import timedelta

class GoalForm(forms.ModelForm):
    """Form for creating and updating personal goals."""

    # Overriding the target_time field for better user input experience
    # Since DurationField can be complex to input, we will take hours/minutes
    # and convert it to a DurationField in the clean method.
    target_hours = forms.IntegerField(
        min_value=0,
        initial=0,
        label="Target Hours",
        required=False,
        help_text="Total hours you plan to spend on this goal."
    )
    target_minutes = forms.IntegerField(
        min_value=0,
        max_value=59,
        initial=0,
        label="Target Minutes",
        required=False,
        help_text="Additional minutes to add to the target hours."
    )

    class Meta:
        model = Goal
        # Explicitly include editable fields from the model
        fields = (
            'title',
            'description',
            'start_date',
            'end_date',
            'days_of_the_week',
            'importance_level',
        )
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'days_of_the_week': forms.TextInput(attrs={'placeholder': 'e.g., 1111100 for Mon-Fri'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Prefill the target time fields when editing an existing goal
        if self.instance and self.instance.pk and self.instance.target_time:
            total_seconds = int(self.instance.target_time.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes = remainder // 60
            self.fields['target_hours'].initial = hours
            self.fields['target_minutes'].initial = minutes

    # Custom cleaning method to combine hours/minutes into the DurationField (target_time)
    def clean(self):
        cleaned_data = super().clean()

        # Get custom fields
        hours = cleaned_data.get('target_hours') or 0
        minutes = cleaned_data.get('target_minutes') or 0

        # Calculate total duration
        total_duration = timedelta(hours=hours, minutes=minutes)

        if total_duration == timedelta(seconds=0):
            # Enforce that the user sets a target time
            raise forms.ValidationError("You must set a target time (hours or minutes) for your goal.")

        # Assign the calculated duration back to the model's 'target_time' field
        cleaned_data['target_time'] = total_duration

        return cleaned_data

    def save(self, commit=True):
        goal = super().save(commit=False)
        target_time = self.cleaned_data.get('target_time')
        if target_time is not None:
            goal.target_time = target_time

        if commit:
            goal.save()
            self.save_m2m()
        return goal
    
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