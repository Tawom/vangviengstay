from django.contrib import admin
from .models import Motorbike, MotorbikeBooking, MotorbikeReview


@admin.register(Motorbike)
class MotorbikeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'owner', 'price_per_day', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'owner')
    search_fields = ('name', 'description', 'owner__username')
    
    # Organize fields into clean sections in the Admin panel
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'owner', 'category', 'engine_cc')
        }),
        ('Pricing', {
            'fields': ('price_per_day', 'deposit_amount')
        }),
        ('Description & Media', {
            'fields': ('description', 'image_url'),
            'classes': ('collapse',) # Collapsible section to save space
        }),
        ('📍 Pickup Location', {
            'fields': ('pickup_address', 'latitude', 'longitude'),
            'description': '💡 Tip: Find coordinates by right-clicking on Google Maps and copying the numbers.'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(MotorbikeBooking)
class MotorbikeBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'motorbike', 'guest', 'start_date', 'end_date', 'status', 'total_price')
    list_filter = ('status', 'start_date')
    search_fields = ('guest__username', 'motorbike__name', 'guest_phone')
    readonly_fields = ('total_price', 'deposit_amount', 'created_at')


@admin.register(MotorbikeReview)
class MotorbikeReviewAdmin(admin.ModelAdmin):
    list_display = ('motorbike', 'guest', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('motorbike__name', 'guest__username', 'comment')
    readonly_fields = ('booking', 'motorbike', 'guest', 'created_at')