from django import forms
from .models import Tour, TourBooking, TourReview


class TourBookingForm(forms.ModelForm):
    """Form for creating a new tour booking."""
    class Meta:
        model = TourBooking
        fields = ['booking_date', 'number_of_people', 'pickup_option', 'pickup_location', 'guest_phone']
        widgets = {
            'booking_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition'
            }),
            'number_of_people': forms.NumberInput(attrs={
                'min': 1,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition'
            }),
            'pickup_option': forms.RadioSelect(attrs={
                'class': 'text-green-600 focus:ring-green-500'
            }),
            'pickup_location': forms.TextInput(attrs={
                'id': 'id_pickup_location',
                'placeholder': 'e.g., Vang Vieng Central Lodge, Room 203, or near the bus station',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition'
            }),
            'guest_phone': forms.TextInput(attrs={
                'placeholder': '+856 20 XXXX XXXX',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ✅ Form-level: pickup_location is not required. Model's clean() enforces it when pickup_option == 'vehicle'
        self.fields['pickup_location'].required = False


class TourReviewForm(forms.ModelForm):
    """Form for submitting a review after a completed tour."""
    class Meta:
        model = TourReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition bg-white'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition resize-none',
                'placeholder': 'Tell us about your experience (optional)...'
            }),
        }


class TourManagementForm(forms.ModelForm):
    """Form for owners to add/edit their tour properties."""
    class Meta:
        model = Tour
        fields = [
            'operator_name', 'name', 'description', 'price_per_person', 'duration_hours', 
            'max_capacity', 'departure_time', 'latitude', 'longitude', 
            'main_image_url', 'is_active'
        ]
        widgets = {
            'operator_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none',
                'placeholder': 'e.g., Jacky Adventure, Vang Vieng Trekking Co.'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none',
                'placeholder': 'e.g., Rock Climbing Intro Course'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none',
                'placeholder': 'Describe the tour, what is included, safety info, etc.'
            }),
            'price_per_person': forms.NumberInput(attrs={
                'step': '0.01', 
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none'
            }),
            'duration_hours': forms.NumberInput(attrs={
                'step': '0.5', 
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none'
            }),
            'max_capacity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none'
            }),
            'departure_time': forms.TimeInput(attrs={
                'type': 'time', 
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none'
            }),
            'latitude': forms.NumberInput(attrs={
                'step': '0.000001', 
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none',
                'placeholder': '18.9385'
            }),
            'longitude': forms.NumberInput(attrs={
                'step': '0.000001', 
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none',
                'placeholder': '102.4433'
            }),
            'main_image_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none',
                'placeholder': 'https://...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-green-600 rounded focus:ring-green-500'
            }),
        }
        labels = {
            'is_active': 'Publish this tour (Visible to guests)',
        }