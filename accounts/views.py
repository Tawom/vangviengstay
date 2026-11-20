from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
# Adjust these imports based on where your forms and models are located
from guesthouse.forms import EmailSignupForm, PhoneSignupForm
from .models import EmailVerificationToken, Profile  # Use 'accounts.models' if Profile is there


# ==========================================
# 1. BASIC SIGNUP (Optional, if still needed)
# ==========================================
def signup(request):
    """Basic user registration (Fallback)."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Ensure profile exists
            Profile.objects.get_or_create(user=user)
            
            login(request, user)
            messages.success(request, 'Welcome! Your account has been created successfully.')
            return redirect('owner_dashboard')
    else:
        form = UserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})


# ==========================================
# 2. EMAIL SIGNUP WITH VERIFICATION (Recommended)
# ==========================================
def signup_email(request):
    """User registration with email and verification token."""
    if request.method == 'POST':
        form = EmailSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # 1. Ensure Profile exists and mark email as unverified
            profile, created = Profile.objects.get_or_create(user=user)
            profile.email_verified = False
            profile.save()
            
            # 2. Add to Owner group automatically
            owner_group, created = Group.objects.get_or_create(name='Owner')
            user.groups.add(owner_group)
            
            # 3. Create secure verification token
            token = EmailVerificationToken.objects.create(user=user)
            
            # 4. Send verification email
            verification_link = f"{request.scheme}://{request.get_host()}/accounts/verify-email/{token.token}/"
            send_mail(
                subject='Verify your email - Vang Vieng Stay',
                message=(
                    f'Hi {user.username},\n\n'
                    f'Please click the link below to verify your email:\n\n'
                    f'{verification_link}\n\n'
                    f'This link will expire in 24 hours.\n\n'
                    f'Thank you!'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            # 5. Log in and redirect with helpful messages
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Please check your email to verify your account.')
            messages.warning(request, '⚠️ Please verify your email to unlock all dashboard features.')
            return redirect('owner_dashboard')
    else:
        form = EmailSignupForm()
    
    return render(request, 'guesthouse/signup_email.html', {'form': form})


# ==========================================
# 3. PHONE SIGNUP WITH VERIFICATION (Recommended)
# ==========================================

def signup_phone(request):
    """User registration with phone number."""
    if request.method == 'POST':
        form = PhoneSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # ✅ Add to Owner group
            owner_group, created = Group.objects.get_or_create(name='Owner')
            user.groups.add(owner_group)
            
            # ✅ Ensure profile exists and save phone number
            profile, created = Profile.objects.get_or_create(user=user)
            phone_number = form.cleaned_data.get('phone_number')
            if phone_number:
                profile.phone_number = phone_number
                profile.phone_verified = False # Mark as unverified until OTP is entered
                profile.save()
                
                # (Optional: Add your OTP sending logic here)
                messages.info(request, f'📱 We sent a code to {phone_number}.')
            
            login(request, user)
            messages.success(request, f'Welcome {user.username}!')
            return redirect('owner_dashboard') # Or redirect to OTP verification page
    else:
        form = PhoneSignupForm()
    
    return render(request, 'guesthouse/signup_phone.html', {'form': form})