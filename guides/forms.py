from django import forms
from .models import Guide, GuideBooking, GuideReview


# ==========================================
# 1. GUEST BOOKING FORM
# ==========================================

class GuideBookingForm(forms.ModelForm):
    """Form for guests to book a local guide."""
    
    # Use a dropdown for duration to make it user-friendly
    DURATION_CHOICES = [
        ('1', '1 Hour'),
        ('2', '2 Hours'),
        ('3', '3 Hours'),
        ('4', 'Half Day (4 Hours)'),
        ('5', '5 Hours'),
        ('6', '6 Hours'),
        ('7', '7 Hours'),
        ('8', 'Full Day (8 Hours)'),
    ]
    duration_hours = forms.ChoiceField(
        choices=DURATION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition bg-white'
        })
    )
    
    class Meta:
        model = GuideBooking
        fields = ['booking_date', 'start_time', 'duration_hours', 'meeting_location', 'guest_phone']
        widgets = {
            'booking_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition'
            }),
            'meeting_location': forms.TextInput(attrs={
                'placeholder': 'e.g., Vang Vieng Central Lodge, near the bus station',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition'
            }),
            'guest_phone': forms.TextInput(attrs={
                'placeholder': '+856 20 XXXX XXXX',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition'
            }),
        }


# ==========================================
# 2. GUEST REVIEW FORM
# ==========================================

class GuideReviewForm(forms.ModelForm):
    """Form for submitting a review after a completed guide booking."""
    class Meta:
        model = GuideReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition bg-white'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition resize-none',
                'placeholder': 'Tell us about your experience with the guide (optional)...'
            }),
        }


# ==========================================
# 3. OWNER MANAGEMENT FORM
# ==========================================

class GuideManagementForm(forms.ModelForm):
    """Form for owners to add/edit their guide profiles."""
    class Meta:
        model = Guide
        fields = [
            'name', 'languages', 'expertise', 'bio', 
            'hourly_rate', 'half_day_rate', 'full_day_rate',
            'photo_url', 'contact_number', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g., Somchai Vongphachan',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'languages': forms.TextInput(attrs={
                'placeholder': 'e.g., English, French, Lao',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'expertise': forms.TextInput(attrs={
                'placeholder': 'e.g., Motorbike routes, hidden cafes, photography',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Brief introduction and what the guide offers...',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'step': '0.01',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'half_day_rate': forms.NumberInput(attrs={
                'step': '0.01',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'full_day_rate': forms.NumberInput(attrs={
                'step': '0.01',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'photo_url': forms.URLInput(attrs={
                'placeholder': 'https://example.com/photo.jpg',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'contact_number': forms.TextInput(attrs={
                'placeholder': '+856 20 XXXX XXXX',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-purple-600 rounded focus:ring-purple-500'
            }),
        }
        labels = {
            'is_active': 'Publish this guide (Visible to guests)',
            'hourly_rate': 'Hourly Rate (₭)',
            'half_day_rate': 'Half Day Rate - up to 4 hours (₭)',
            'full_day_rate': 'Full Day Rate - up to 8 hours (₭)',
        }