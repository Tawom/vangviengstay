from django.db import models
from django.urls import reverse


class TripPlan(models.Model):
    BUDGET_CHOICES = [
        ('budget', 'Budget-friendly'),
        ('mid', 'Mid-range'),
        ('premium', 'Premium'),
    ]
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('planned', 'Itinerary Sent'),
        ('booked', 'Booked'),
        ('completed', 'Completed'),
    ]

    # Contact info
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    whatsapp = models.CharField(max_length=30, blank=True, null=True,
                                help_text="Include country code, e.g. +85620...")

    # Trip details
    travel_date_start = models.DateField()
    travel_date_end = models.DateField()
    group_size = models.PositiveIntegerField(default=1)
    interests = models.CharField(max_length=255,
                                 help_text="Comma-separated: adventure,motorbike,food,relaxing")
    budget = models.CharField(max_length=20, choices=BUDGET_CHOICES, default='mid')
    special_requests = models.TextField(blank=True)

    # Internal tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    notes = models.TextField(blank=True, help_text="Internal notes for your team")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.travel_date_start} ({self.group_size} pax)"

    def get_interests_list(self):
        return [i.strip() for i in self.interests.split(',') if i.strip()]

    def get_absolute_url(self):
        return reverse('trip_plan_success')