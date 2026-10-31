from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta


# ==========================================
# 1. TOUR MODEL
# ==========================================

class Tour(models.Model):
    name = models.CharField(max_length=200, help_text="e.g., Rock Climbing Intro Course")
    
    # ✅ NEW: Operator/Business Name
    operator_name = models.CharField(
        max_length=200, 
        help_text="e.g., Jacky Adventure, Vang Vieng Trekking Co."
    )
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tours')
    description = models.TextField()
    price_per_person = models.DecimalField(max_digits=8, decimal_places=2)
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1, help_text="Duration in hours")
    max_capacity = models.PositiveIntegerField(help_text="Maximum number of people per tour")
    departure_time = models.TimeField(help_text="Daily departure time")
    main_image_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Office Location Coordinates
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, 
        help_text="e.g., 18.933500 (Office location for maps)"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, 
        help_text="e.g., 102.453300 (Office location for maps)"
    )

    def __str__(self):
        return f"{self.name} ({self.operator_name})"
    
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
# 2. TOUR BOOKING MODEL
# ==========================================

class TourBooking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Payment'),
        ('confirmed', 'Confirmed (Paid)'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )

    PICKUP_CHOICES = (
        ('vehicle', 'Pick me up from my guesthouse'),
        ('self', "I'll make my own way to the office"),
    )
    
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='bookings')
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tour_bookings')
    booking_date = models.DateField(help_text="Date of the tour")
    number_of_people = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attended = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Pickup & Contact Fields
    pickup_option = models.CharField(
        max_length=10, 
        choices=PICKUP_CHOICES, 
        default='vehicle',
        help_text="How will you get to the tour starting point?"
    )
    pickup_location = models.CharField(
        max_length=300, 
        blank=True,
        help_text="Guesthouse name, address, or landmark (only if vehicle pickup)"
    )
    guest_phone = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Your phone number with country code for WhatsApp (e.g., +85620...)"
    )

    def __str__(self):
        return f"{self.guest.username} - {self.tour.name} on {self.booking_date} ({self.number_of_people} people)"

    def clean(self):
        """Comprehensive validation for tour bookings."""
        super().clean()

        # Rule 1: Must book at least 1 person
        if self.number_of_people < 1:
            raise ValidationError("You must book at least 1 person.")

        # Rule 2: Cannot book in the past
        if self.booking_date and self.booking_date < timezone.now().date():
            raise ValidationError("You cannot book a tour in the past.")

        # Rule 3: Pickup location required if vehicle pickup selected
        if self.pickup_option == 'vehicle' and not self.pickup_location.strip():
            raise ValidationError('Please provide your pickup location (guesthouse name or address).')

        # Rule 4: Check capacity (only for active bookings)
        if self.status in ('cancelled', 'refunded'):
            return

        if self.tour_id and self.booking_date and self.number_of_people:
            # Get all confirmed/pending bookings for this tour on this date
            existing_bookings = TourBooking.objects.filter(
                tour_id=self.tour_id,
                booking_date=self.booking_date,
                status__in=['pending', 'confirmed']
            )

            # Exclude this booking if we're editing it
            if self.pk:
                existing_bookings = existing_bookings.exclude(pk=self.pk)

            # Calculate total people already booked
            total_booked = sum(booking.number_of_people for booking in existing_bookings)

            # Check if adding this booking would exceed capacity
            if total_booked + self.number_of_people > self.tour.max_capacity:
                available_spots = self.tour.max_capacity - total_booked
                raise ValidationError(
                    f"Only {available_spots} spots available. You requested {self.number_of_people}."
                )

    def save(self, *args, **kwargs):
        """Calculate total price before saving."""
        if self.tour_id and self.number_of_people:
            self.total_price = self.number_of_people * self.tour.price_per_person
        super().save(*args, **kwargs)

    def get_pickup_time_display(self):
        """Return a human-readable pickup time (30 mins before departure)."""
        if self.pickup_option == 'vehicle':
            # Combine date and time, subtract 30 minutes
            departure_dt = datetime.combine(self.booking_date, self.tour.departure_time)
            pickup_dt = departure_dt - timedelta(minutes=30)
            return pickup_dt.strftime("%H:%M")
        return None


# ==========================================
# 3. TOUR REVIEW MODEL
# ==========================================

class TourReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    booking = models.OneToOneField(TourBooking, on_delete=models.CASCADE, related_name='tour_review')
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='reviews')
    guest = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # Always show newest first

    def __str__(self):
        return f"Review for {self.tour.name} by {self.guest.username}"