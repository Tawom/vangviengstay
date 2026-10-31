from django import forms
from .models import Motorbike, MotorbikeBooking, MotorbikeReview


class MotorbikeBookingForm(forms.ModelForm):
    """Form for creating a new motorbike booking."""
    class Meta:
        model = MotorbikeBooking
        fields = ['start_date', 'end_date', 'guest_phone', 'passport_number']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition'
            }),
            'guest_phone': forms.TextInput(attrs={
                'placeholder': '+856 20 XXXX XXXX',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition'
            }),
            'passport_number': forms.TextInput(attrs={
                'placeholder': 'Optional: For deposit record',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition'
            }),
        }


class MotorbikeReviewForm(forms.ModelForm):
    """Form for submitting a review after a completed motorbike rental."""
    class Meta:
        model = MotorbikeReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition bg-white'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition resize-none',
                'placeholder': 'Tell us about your experience (optional)...'
            }),
        }


class MotorbikeManagementForm(forms.ModelForm):
    """Form for owners to add/edit their motorbike properties."""
    class Meta:
        model = Motorbike
        fields = [
            'name', 'category', 'engine_cc', 'price_per_day', 'deposit_amount',
            'description', 'image_url', 'latitude', 'longitude', 'pickup_address', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g., Honda Click 125cc',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none'
            }),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none bg-white'}),
            'engine_cc': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none'}),
            'price_per_day': forms.NumberInput(attrs={'step': '0.01', 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none'}),
            'deposit_amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none'}),
            'image_url': forms.URLInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none'}),
            'latitude': forms.NumberInput(attrs={
                'step': '0.000001',
                'placeholder': 'e.g., 18.929700',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none'
            }),
            'longitude': forms.NumberInput(attrs={
                'step': '0.000001',
                'placeholder': 'e.g., 102.446700',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none'
            }),
            'pickup_address': forms.TextInput(attrs={
                'placeholder': 'e.g., Near the night market, Vang Vieng',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-orange-600 rounded focus:ring-orange-500'}),
        }