from django import forms
from django.utils import timezone
from .models import TripPlan


class TripPlanForm(forms.ModelForm):
    INTEREST_CHOICES = [
        ('adventure', '🏞️ Adventure (Kayaking, Hiking, Waterfalls)'),
        ('motorbike', '🏍️ Motorbike / Buggy Car Exploration'),
        ('food', '🍜 Local Food & Culture'),
        ('relaxing', '🧘 Relaxing & Chill'),
        ('viewpoints', '📸 Viewpoints & Photography'),
    ]

    interests = forms.MultipleChoiceField(
        choices=INTEREST_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="What sounds most exciting to you?"
    )

    class Meta:
        model = TripPlan
        fields = ['name', 'email', 'whatsapp', 'travel_date_start',
                  'travel_date_end', 'group_size', 'interests', 'budget',
                  'special_requests']
        widgets = {
            'travel_date_start': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date().isoformat()}),
            'travel_date_end': forms.DateInput(attrs={'type': 'date'}),
            'special_requests': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email')
        whatsapp = cleaned.get('whatsapp')
        if not email and not whatsapp:
            raise forms.ValidationError("Please provide either an email or WhatsApp number so we can reach you.")

        start = cleaned.get('travel_date_start')
        end = cleaned.get('travel_date_end')
        if start and end and end < start:
            raise forms.ValidationError("Return date must be after departure date.")

        if cleaned.get('group_size', 0) < 1:
            raise forms.ValidationError("Group size must be at least 1.")

        # Convert interests list to comma-separated string
        if 'interests' in cleaned:
            cleaned['interests'] = ','.join(cleaned['interests'])

        return cleaned