from django.contrib import admin
from .models import Tour, TourBooking, TourReview


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    # ✅ Added 'operator_name' to list display and search fields
    list_display = ('name', 'operator_name', 'price_per_person', 'duration_hours', 'max_capacity', 'is_active')
    list_filter = ('is_active', 'duration_hours')
    search_fields = ('name', 'operator_name', 'description')
    
    fieldsets = (
        ('Basic Information', {
            # ✅ Added 'operator_name' right after 'name'
            'fields': ('name', 'operator_name', 'owner', 'description', 'is_active')
        }),
        ('Tour Details', {
            'fields': ('price_per_person', 'duration_hours', 'max_capacity', 'departure_time')
        }),
        ('Office Location (Coordinates)', {
            'fields': ('latitude', 'longitude'),
            'description': 'Optional: Add coordinates so guests can find the tour office on a map.'
        }),
        ('Media', {
            'fields': ('main_image_url',)
        }),
    )


@admin.register(TourBooking)
class TourBookingAdmin(admin.ModelAdmin):
    list_display = ('guest', 'tour', 'booking_date', 'pickup_option', 'total_price', 'status', 'attended')
    list_filter = ('status', 'attended', 'pickup_option', 'booking_date')
    # ✅ Added 'tour__operator_name' to search fields for easier lookup
    search_fields = ('guest__username', 'tour__name', 'tour__operator_name', 'pickup_location')


@admin.register(TourReview)
class TourReviewAdmin(admin.ModelAdmin):
    list_display = ('tour', 'guest', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    # ✅ Added 'tour__operator_name' to search fields for easier lookup
    search_fields = ('guest__username', 'tour__name', 'tour__operator_name', 'comment')