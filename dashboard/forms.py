# In dashboard/forms.py (New File)

from django import forms
from .models import Goal, TimeLog
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

"""
class GoalForm(forms.ModelForm):
    

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
"""

from datetime import timedelta
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

DAY_CHOICES = [
    ('0', 'Mon'),
    ('1', 'Tue'),
    ('2', 'Wed'),
    ('3', 'Thu'),
    ('4', 'Fri'),
    ('5', 'Sat'),
    ('6', 'Sun'),
]

IMPORTANCE_CHOICES = [
    (1, '1 (Low)'),
    (2, '2'),
    (3, '3 (Medium)'),
    (4, '4'),
    (5, '5 (High)'),
]

TW_INPUT = "mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
TW_TEXTAREA = "mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
TW_RADIO = "h-4 w-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"

class GoalForm(forms.ModelForm):
    """Form for creating and updating personal goals (without 'completed' checkbox)."""

    target_hours = forms.IntegerField(
        min_value=0,
        initial=1,
        label="Target Hours",
        required=False,
        help_text="How many hours do you plan to spend in total?",
        widget=forms.NumberInput(attrs={"min": 0, "step": 1, "placeholder": "e.g., 10", "class": TW_INPUT})
    )
    target_minutes = forms.IntegerField(
        min_value=0,
        max_value=59,
        initial=0,
        label="Target Minutes",
        required=False,
        help_text="Additional minutes (0–59).",
        widget=forms.NumberInput(attrs={"min": 0, "max": 59, "step": 1, "placeholder": "e.g., 30", "class": TW_INPUT})
    )

    days_selection = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="Active Days",
        required=False,
        help_text="Pick the days you plan to work on this goal (optional).",
    )

    class Meta:
        model = Goal
        fields = (
            'title',
            'description',
            'start_date',
            'end_date',
            'importance_level',
        )
        widgets = {
            'title': forms.TextInput(attrs={"placeholder": "e.g., Study Data Structures", "class": TW_INPUT}),
            'description': forms.Textarea(attrs={"rows": 4, "placeholder": "Describe your goal...", "class": TW_TEXTAREA}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': TW_INPUT}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': TW_INPUT}),
            'importance_level': forms.RadioSelect(choices=IMPORTANCE_CHOICES, attrs={"class": TW_RADIO}),
        }
        labels = {
            'importance_level': 'Importance',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Prefill defaults for new goals
        if not self.instance or not self.instance.pk:
            self.fields['start_date'].initial = timezone.localdate()
            self.fields['days_selection'].initial = ['0','1','2','3','4']

        # Prefill time + days if editing
        if self.instance and self.instance.pk:
            if self.instance.target_time:
                total_seconds = int(self.instance.target_time.total_seconds())
                h, rem = divmod(total_seconds, 3600)
                m = rem // 60
                self.fields['target_hours'].initial = h
                self.fields['target_minutes'].initial = m

            days_str = self.instance.days_of_the_week
            if days_str:
                self.fields['days_selection'].initial = [str(i) for i, c in enumerate(days_str) if c == '1']

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        hours = cleaned.get('target_hours') or 0
        minutes = cleaned.get('target_minutes') or 0

        if start and end and end < start:
            raise ValidationError("End date cannot be before the start date.")

        total = timedelta(hours=hours, minutes=minutes)
        if total == timedelta(0):
            raise ValidationError("Please set a non-zero target time (hours or minutes).")

        cleaned['target_time'] = total
        return cleaned

    def save(self, commit=True):
        goal = super().save(commit=False)

        goal.completed = False  # Force to False by default

        # Combine hours/minutes into target_time
        tt = self.cleaned_data.get('target_time')
        if tt:
            goal.target_time = tt

        # Encode selected days
        selected = set(self.cleaned_data.get('days_selection', []))
        goal.days_of_the_week = "".join('1' if str(i) in selected else '0' for i in range(7))

        goal.updated_at = timezone.now()
        if commit:
            goal.save()
        return goal


    
class TimeLogForm(forms.ModelForm):
    """
    Form for logging time spent on a goal.
    """
    minutes = forms.FloatField(
        label='Time Spent (in minutes)',
        min_value=1.0,
        widget=forms.NumberInput(attrs={
            'min': 1, 
            'step': 0.1, 
            'placeholder': 'Enter minutes logged (e.g., 90.5)'
            })
    )

    log_date = forms.DateField(
        label='Date Logged',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = TimeLog
        # Note: We exclude 'duration' here, as we calculate it in the view
        # or handle it in the clean method before saving.
        # We include the log_date which is now defined above.
        fields = ('minutes', 'log_date',) 

    def clean_minutes(self):
        minutes = self.cleaned_data.get('minutes')
        # This form field already has min_value=1.0, but this is a redundant safety check
        if minutes is not None and minutes <= 0:
            raise forms.ValidationError("Time logged must be at least 1 minute.")
        return minutes
    
    def save(self, commit=True):
        """
        Ensure 'minutes' is saved as an integer if the model field expects it.
        """
        instance = super().save(commit=False)
        # Convert float to int safely (e.g., 90.5 → 90)
        instance.minutes = int(round(self.cleaned_data['minutes']))
        if commit:
            instance.save()
        return instance