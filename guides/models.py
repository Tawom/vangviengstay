from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


# ==========================================
# 1. GUIDE PROFILE MODEL
# ==========================================

class Guide(models.Model):
    """Represents a local guide offering their services on the platform."""
    
    name = models.CharField(max_length=100, help_text="Guide's full name")
    
    # ✅ NEW: Agency/Operator Name (Optional)
    operator_name = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Agency or business name (Optional, e.g., 'Vang Vieng Local Guides Co.')"
    )
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guides')
    languages = models.CharField(max_length=200, help_text="e.g., English, French, Lao, Chinese")
    expertise = models.CharField(max_length=200, help_text="e.g., Motorbike routes, hidden cafes, photography")
    bio = models.TextField(help_text="Brief introduction and what they offer")
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, help_text="Price per hour in USD")
    half_day_rate = models.DecimalField(max_digits=6, decimal_places=2, help_text="Up to 4 hours")
    full_day_rate = models.DecimalField(max_digits=6, decimal_places=2, help_text="Up to 8 hours")
    photo_url = models.URLField(blank=True, null=True, help_text="Link to guide's profile photo")
    contact_number = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Guide's WhatsApp/phone number with country code (e.g., +85620...)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.operator_name:
            return f"{self.name} - {self.operator_name}"
        return self.name
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0.0
        return round(sum(review.rating for review in reviews) / len(reviews), 1)

    @property
    def review_count(self):
        return self.reviews.count()


# ==========================================
# 2. GUIDE BOOKING MODEL
# ==========================================

class GuideBooking(models.Model):
    """Represents a booking made by a guest for a local guide."""
    
    STATUS_CHOICES = (
        ('pending', 'Pending Verification'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name='bookings')
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guide_bookings')
    booking_date = models.DateField()
    start_time = models.TimeField(help_text="e.g., 08:00:00")
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1, help_text="Duration in hours")
    total_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attended = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Meeting & Contact Information
    meeting_location = models.CharField(
        max_length=300, 
        help_text="Where should the guide meet you? (e.g., hotel name, address, or landmark)"
    )
    guest_phone = models.CharField(
        max_length=20, 
        blank=True, 
        help_text="Your phone number with country code for WhatsApp (e.g., +85620...)"
    )

    def __str__(self):
        return f"Booking for {self.guide.name} by {self.guest.username} on {self.booking_date}"

    def clean(self):
        """Validation for guide bookings."""
        super().clean()

        # Cannot book in the past
        if self.booking_date and self.booking_date < timezone.now().date():
            raise ValidationError("You cannot book a guide for a past date.")

        # Duration must be positive
        if self.duration_hours and self.duration_hours <= 0:
            raise ValidationError("Duration must be at least 1 hour.")

        # Duration cannot exceed 8 hours (max for full day)
        if self.duration_hours and self.duration_hours > 8:
            raise ValidationError("Maximum booking duration is 8 hours (full day).")

    def save(self, *args, **kwargs):
        """Calculate total price based on duration and guide rates."""
        if self.guide_id and self.duration_hours:
            if self.duration_hours <= 1:
                # Hourly rate for 1 hour or less
                self.total_price = self.duration_hours * self.guide.hourly_rate
            elif self.duration_hours <= 4:
                # Half day rate (flat)
                self.total_price = self.guide.half_day_rate
            else:
                # Full day rate (flat)
                self.total_price = self.guide.full_day_rate
        super().save(*args, **kwargs)


# ==========================================
# 3. GUIDE REVIEW MODEL
# ==========================================

class GuideReview(models.Model):
    """Represents a review left by a guest after a guide booking."""
    
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    booking = models.OneToOneField(GuideBooking, on_delete=models.CASCADE, related_name='guide_review')
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name='reviews')
    guest = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.guide.name} by {self.guest.username}"