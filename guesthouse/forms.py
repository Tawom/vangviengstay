from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Booking, Guesthouse, GuesthouseReview


# ==========================================
# 1. USER REGISTRATION FORM
# ==========================================

class EmailSignupForm(UserCreationForm):
    """Signup form requiring an email address."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'your@email.com',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition'
        }),
        help_text='Required. We will send your booking confirmations here.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Choose a username',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition'
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Create a strong password',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirm your password',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition'
        })


class PhoneSignupForm(UserCreationForm):
    """Signup form requiring a phone number for OTP verification."""
    phone_number = forms.CharField(
        required=True,
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': '+856 20 XXXX XXXX',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition'
        }),
        help_text='Required. Used for booking confirmations and password reset via OTP.'
    )

    class Meta:
        model = User
        fields = ('username', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Choose a username',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition'
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Create a strong password',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirm your password',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition'
        })

# ==========================================
# 2. GUESTHOUSE BOOKING FORM
# ==========================================

class BookingForm(forms.ModelForm):
    """Form for creating a new guesthouse booking with dynamic room selection."""
    
    class Meta:
        model = Booking
        fields = ['check_in', 'check_out', 'guests', 'room_type']
        widgets = {
            'check_in': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition'
            }),
            'check_out': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition'
            }),
            'guests': forms.NumberInput(attrs={
                'min': 1,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition'
            }),
            'room_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition bg-white'
            })
        }

    def __init__(self, *args, **kwargs):
        # Pop the guesthouse object passed from the view
        guesthouse = kwargs.pop('guesthouse', None)
        super().__init__(*args, **kwargs)
        
        # If the guesthouse doesn't allow room selection, hide the field and set default
        if guesthouse and not guesthouse.allow_room_selection:
            self.fields['room_type'].widget = forms.HiddenInput()
            self.fields['room_type'].initial = 'standard'
            self.fields['room_type'].required = False


# ==========================================
# 3. GUESTHOUSE REVIEW FORM
# ==========================================

class GuesthouseReviewForm(forms.ModelForm):
    """Form for submitting a review after a completed guesthouse stay."""
    
    class Meta:
        model = GuesthouseReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition bg-white'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition resize-none',
                'placeholder': 'Tell us about your stay (optional)...'
            }),
        }


# ==========================================
# 4. GUESTHOUSE MANAGEMENT FORM (OWNER DASHBOARD)
# ==========================================

class GuesthouseManagementForm(forms.ModelForm):
    """Form for owners to add/edit their guesthouse properties."""
    
    class Meta:
        model = Guesthouse
        fields = [
            'name', 'city', 'address', 'description', 'price_per_night', 
            'latitude', 'longitude', 'allow_room_selection', 'main_image_url', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'city': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'price_per_night': forms.NumberInput(attrs={'step': '0.01', 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'latitude': forms.NumberInput(attrs={'step': '0.000001', 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001', 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'main_image_url': forms.URLInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'allow_room_selection': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-blue-600 rounded focus:ring-blue-500'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-blue-600 rounded focus:ring-blue-500'}),
        }
        labels = {
            'is_active': 'Publish this guesthouse (Visible to guests)',
            'allow_room_selection': 'Allow guests to select specific room types (Single, Double, etc.)'
        }