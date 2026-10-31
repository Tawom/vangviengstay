from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date


# ==========================================
# 1. MOTORBIKE MODEL
# ==========================================

class Motorbike(models.Model):
    CATEGORY_CHOICES = (
        ('semi_auto', 'Semi-Automatic (e.g., Honda Wave)'),
        ('automatic', 'Automatic Scooter (e.g., Honda Click)'),
        ('manual', 'Manual (e.g., Honda CRF, Dirt Bike)'),
    )
    
    name = models.CharField(max_length=200, help_text="e.g., Honda Click 125cc")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='motorbikes')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    engine_cc = models.PositiveIntegerField(help_text="e.g., 110, 125, 150")
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in LAK")
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Security deposit in LAK (or passport)")
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    
    # ✅ Location Coordinates
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, 
        blank=True, null=True,
        help_text="e.g., 18.9297 (Vang Vieng center)"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, 
        blank=True, null=True,
        help_text="e.g., 102.4467 (Vang Vieng center)"
    )
    pickup_address = models.CharField(
        max_length=300, 
        blank=True, 
        null=True,
        help_text="Full address where guests can pick up the motorbike"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    @property
    def average_rating(self):
        """Calculate average rating from all reviews."""
        reviews = self.reviews.all()
        if not reviews:
            return 0.0
        return round(sum(review.rating for review in reviews) / len(reviews), 1)

    @property
    def review_count(self):
        """Count total number of reviews."""
        return self.reviews.count()


# ==========================================
# 2. MOTORBIKE BOOKING MODEL
# ==========================================

class MotorbikeBooking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    motorbike = models.ForeignKey(Motorbike, on_delete=models.CASCADE, related_name='bookings')
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='motorbike_bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Contact & Collateral Info
    guest_phone = models.CharField(max_length=20, help_text="For WhatsApp coordination")
    passport_number = models.CharField(max_length=50, blank=True, help_text="Optional: Passport number for deposit record")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.guest.username} - {self.motorbike.name} ({self.start_date} to {self.end_date})"

    def clean(self):
        """Validate dates and prevent past bookings."""
        super().clean()
        if self.start_date and self.start_date < date.today():
            raise ValidationError("You cannot rent a motorbike for a past date.")
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date must be after or equal to the start date.")

    def save(self, *args, **kwargs):
        """Calculate total price and deposit before saving."""
        if self.start_date and self.end_date and self.motorbike:
            days = (self.end_date - self.start_date).days + 1
            self.total_price = days * self.motorbike.price_per_day
            self.deposit_amount = self.motorbike.deposit_amount
        super().save(*args, **kwargs)


# ==========================================
# 3. MOTORBIKE REVIEW MODEL
# ==========================================

class MotorbikeReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    booking = models.OneToOneField(MotorbikeBooking, on_delete=models.CASCADE, related_name='motorbike_review')
    motorbike = models.ForeignKey(Motorbike, on_delete=models.CASCADE, related_name='reviews')
    guest = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.motorbike.name} by {self.guest.username}"