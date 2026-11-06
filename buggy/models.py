from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date


class BuggyCar(models.Model):
    SIZE_CHOICES = (
        ('2_seat', '2-Seat Buggy'),
        ('4_seat', '4-Seat Buggy'),
    )
    
    name = models.CharField(max_length=200, help_text="e.g., Yamaha Rhino 2-Seater")
    
    # ✅ NEW: Operator name (shown to customers, like "Vang Vieng Buggy Adventures")
    operator_name = models.CharField(
        max_length=200, 
        help_text="Business name shown to customers (e.g., 'Vang Vieng Buggy Adventures')"
    )
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buggy_cars')
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    
    # Hourly pricing + Full Day
    price_2_hours = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price for 2 hours")
    price_3_hours = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price for 3 hours")
    price_4_hours = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price for 4 hours")
    price_5_hours = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price for 5 hours")
    price_6_hours = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price for 6 hours")
    price_full_day = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price for a full day rental")
    
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Security deposit in LAK")
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    
    # Location
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    pickup_address = models.CharField(max_length=300, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_size_display()}) - {self.operator_name}"
    
    def get_price_for_duration(self, hours):
        """Get the price based on rental duration."""
        price_map = {
            2: self.price_2_hours,
            3: self.price_3_hours,
            4: self.price_4_hours,
            5: self.price_5_hours,
            6: self.price_6_hours,
            24: self.price_full_day,  # Map 24 hours to Full Day price
        }
        return price_map.get(hours, 0)
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0.0
        return round(sum(review.rating for review in reviews) / len(reviews), 1)

    @property
    def review_count(self):
        return self.reviews.count()


class BuggyCarBooking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    # Duration choices with Full Day mapped to 24 hours
    DURATION_CHOICES = [
        (2, '2 Hours'),
        (3, '3 Hours'),
        (4, '4 Hours'),
        (5, '5 Hours'),
        (6, '6 Hours'),
        (24, 'Full Day'),
    ]
    
    buggy_car = models.ForeignKey(BuggyCar, on_delete=models.CASCADE, related_name='bookings')
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buggy_bookings')
    booking_date = models.DateField()
    start_time = models.TimeField(help_text="Start time (e.g., 08:00)")
    duration_hours = models.PositiveIntegerField(choices=DURATION_CHOICES)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    guest_phone = models.CharField(max_length=20, help_text="For WhatsApp coordination")
    passport_number = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        duration_display = "Full Day" if self.duration_hours == 24 else f"{self.duration_hours} Hours"
        return f"{self.guest.username} - {self.buggy_car.name} ({self.booking_date}, {duration_display})"

    def clean(self):
        super().clean()
        if self.booking_date and self.booking_date < date.today():
            raise ValidationError("You cannot book a buggy car for a past date.")
        if self.duration_hours and self.duration_hours not in [2, 3, 4, 5, 6, 24]:
            raise ValidationError("Duration must be 2, 3, 4, 5, 6 hours, or Full Day.")

    def save(self, *args, **kwargs):
        if self.buggy_car and self.duration_hours:
            self.total_price = self.buggy_car.get_price_for_duration(self.duration_hours)
            self.deposit_amount = self.buggy_car.deposit_amount
        super().save(*args, **kwargs)


class BuggyCarReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    booking = models.OneToOneField(BuggyCarBooking, on_delete=models.CASCADE, related_name='buggy_review')
    buggy_car = models.ForeignKey(BuggyCar, on_delete=models.CASCADE, related_name='reviews')
    guest = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.buggy_car.name} by {self.guest.username}"