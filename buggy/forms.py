from django import forms
from .models import BuggyCar, BuggyCarBooking, BuggyCarReview


class BuggyCarBookingForm(forms.ModelForm):
    """Form for creating a new buggy car booking."""
    # ✅ UPDATED: Duration choices with Full Day mapped to 24 hours
    DURATION_CHOICES = [
        (2, '2 Hours'),
        (3, '3 Hours'),
        (4, '4 Hours'),
        (5, '5 Hours'),
        (6, '6 Hours'),
        (24, 'Full Day'),
    ]
    
    duration_hours = forms.ChoiceField(
        choices=DURATION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition bg-white'
        })
    )
    
    class Meta:
        model = BuggyCarBooking
        fields = ['booking_date', 'start_time', 'duration_hours', 'guest_phone', 'passport_number']
        widgets = {
            'booking_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition'
            }),
            'guest_phone': forms.TextInput(attrs={
                'placeholder': '+856 20 XXXX XXXX',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition'
            }),
            'passport_number': forms.TextInput(attrs={
                'placeholder': 'Optional: For deposit record',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition'
            }),
        }


class BuggyCarReviewForm(forms.ModelForm):
    """Form for submitting a review after a completed buggy car rental."""
    class Meta:
        model = BuggyCarReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition bg-white'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition resize-none',
                'placeholder': 'Tell us about your experience (optional)...'
            }),
        }


class BuggyCarManagementForm(forms.ModelForm):
    """Form for owners to add/edit their buggy car properties."""
    class Meta:
        model = BuggyCar
        # ✅ UPDATED: Removed 7, 8, 9 hour fields, added price_full_day
        fields = [
            'name', 'size', 'price_2_hours', 'price_3_hours', 'price_4_hours', 
            'price_5_hours', 'price_6_hours', 'price_full_day',
            'deposit_amount', 'description', 'image_url', 
            'latitude', 'longitude', 'pickup_address', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g., Yamaha Rhino 2-Seater',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'size': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none bg-white'
            }),
            'price_2_hours': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Price for 2 hours',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'price_3_hours': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Price for 3 hours',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'price_4_hours': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Price for 4 hours',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'price_5_hours': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Price for 5 hours',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'price_6_hours': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Price for 6 hours',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'price_full_day': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Price for full day rental',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'deposit_amount': forms.NumberInput(attrs={
                'step': '0.01',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'latitude': forms.NumberInput(attrs={
                'step': '0.000001',
                'placeholder': 'e.g., 18.929700',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'longitude': forms.NumberInput(attrs={
                'step': '0.000001',
                'placeholder': 'e.g., 102.446700',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'pickup_address': forms.TextInput(attrs={
                'placeholder': 'e.g., Near the night market, Vang Vieng',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-purple-600 rounded focus:ring-purple-500'
            }),
        }