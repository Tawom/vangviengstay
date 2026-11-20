import secrets
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Profile(models.Model):
    """Extended user profile for contact info and verification status."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Contact Info
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="e.g., +856 20 1234 5678"
    )
    
    # Verification Status
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    # OTP Fields (for phone verification)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def is_otp_expired(self):
        """Check if the OTP has expired (e.g., after 10 minutes)."""
        if not self.otp_created_at:
            return True
        return (timezone.now() - self.otp_created_at).total_seconds() > 600


# ==========================================
# Signals to automatically manage the Profile
# ==========================================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a Profile whenever a new User is created."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Automatically save the Profile when the User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


# ==========================================
# Email Verification Token
# ==========================================

class EmailVerificationToken(models.Model):
    """Token for verifying user email addresses."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_token')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(64)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if the token has expired (24 hours)."""
        return (timezone.now() - self.created_at).total_seconds() > 86400