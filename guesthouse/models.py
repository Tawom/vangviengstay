from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


# ==========================================
# 1. GUESTHOUSE MODEL
# ==========================================

class Guesthouse(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guesthouses')
    city = models.CharField(max_length=100, default='Vang Vieng')
    address = models.TextField(blank=True, help_text="Full street address")
    description = models.TextField()
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Location Coordinates
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, 
        help_text="e.g., 18.933500 (Optional, but recommended for maps)"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, 
        help_text="e.g., 102.453300 (Optional, but recommended for maps)"
    )
    
    # Room Selection Toggle
    allow_room_selection = models.BooleanField(
        default=False, 
        help_text="Enable specific room type selection (Single, Double, etc.) for this property. If disabled, guests will be assigned a standard room upon arrival."
    )
    
    main_image_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
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
# 2. BOOKING MODEL
# ==========================================

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Payment'),
        ('confirmed', 'Confirmed (Paid)'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )

    ROOM_TYPE_CHOICES = (
        ('standard', 'Standard Room (Assigned on Arrival)'),
        ('single', 'Single Room'),
        ('double', 'Double Room'),
        ('twin', 'Twin Room'),
        ('dorm', 'Dorm Bed'),
    )

    guesthouse = models.ForeignKey(Guesthouse, on_delete=models.CASCADE, related_name='bookings')
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    checked_in = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    room_type = models.CharField(
        max_length=20, 
        choices=ROOM_TYPE_CHOICES, 
        default='standard',
        help_text="Type of room requested"
    )

    def __str__(self):
        return f"{self.guest.username} - {self.guesthouse.name} ({self.check_in})"

    def clean(self):
        """Comprehensive validation for guesthouse bookings."""
        super().clean()

        # Rule 1: Check-out must be after Check-in
        if self.check_in and self.check_out and self.check_in >= self.check_out:
            raise ValidationError("Check-out date must be after check-in date.")

        # Rule 2: Cannot book in the past
        if self.check_in and self.check_in < timezone.now().date():
            raise ValidationError("You cannot book a date in the past.")

        # Rule 3: Only ACTIVE bookings (pending or confirmed) should block dates.
        # Cancelled / refunded bookings release the dates immediately.
        if self.status in ('cancelled', 'refunded'):
            return

        if self.guesthouse_id and self.check_in and self.check_out:
            overlapping_bookings = Booking.objects.filter(
                guesthouse_id=self.guesthouse_id,
                status__in=['pending', 'confirmed']
            ).filter(
                check_in__lt=self.check_out,
                check_out__gt=self.check_in
            )

            # Don't count this booking as overlapping with itself (on updates)
            if self.pk:
                overlapping_bookings = overlapping_bookings.exclude(pk=self.pk)

            if overlapping_bookings.exists():
                raise ValidationError(
                    "These dates overlap with an existing pending or confirmed booking."
                )

    def save(self, *args, **kwargs):
        """Calculate total price before saving."""
        if self.guesthouse_id and self.check_in and self.check_out:
            nights = (self.check_out - self.check_in).days
            if nights > 0:
                self.total_price = nights * self.guesthouse.price_per_night
        super().save(*args, **kwargs)


# ==========================================
# 3. GUESTHOUSE REVIEW MODEL
# ==========================================

class GuesthouseReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='guesthouse_review')
    guesthouse = models.ForeignKey(Guesthouse, on_delete=models.CASCADE, related_name='reviews')
    guest = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # Always show newest first

    def __str__(self):
        return f"Review for {self.guesthouse.name} by {self.guest.username}"