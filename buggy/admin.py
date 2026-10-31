from django.contrib import admin
from .models import BuggyCar, BuggyCarBooking, BuggyCarReview


@admin.register(BuggyCar)
class BuggyCarAdmin(admin.ModelAdmin):
    list_display = ('name', 'size', 'owner', 'price_2_hours', 'is_active', 'created_at')
    list_filter = ('size', 'is_active', 'owner')
    search_fields = ('name', 'description', 'owner__username')
    
    # ✅ UPDATED: Removed 7, 8, 9 hour fields, added price_full_day
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'owner', 'size')
        }),
        ('Pricing (LAK)', {
            'fields': ('price_2_hours', 'price_3_hours', 'price_4_hours', 'price_5_hours', 'price_6_hours', 'price_full_day')
        }),
        ('Deposit & Media', {
            'fields': ('deposit_amount', 'description', 'image_url'),
            'classes': ('collapse',)
        }),
        ('📍 Pickup Location', {
            'fields': ('pickup_address', 'latitude', 'longitude'),
            'description': '💡 Tip: Find coordinates by right-clicking on Google Maps.'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(BuggyCarBooking)
class BuggyCarBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'buggy_car', 'guest', 'booking_date', 'duration_hours', 'status', 'total_price')
    list_filter = ('status', 'booking_date')
    search_fields = ('guest__username', 'buggy_car__name', 'guest_phone')
    readonly_fields = ('total_price', 'deposit_amount', 'created_at')


@admin.register(BuggyCarReview)
class BuggyCarReviewAdmin(admin.ModelAdmin):
    list_display = ('buggy_car', 'guest', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('buggy_car__name', 'guest__username', 'comment')