from django.contrib import admin
from django.contrib import messages

from .models import Guesthouse, Booking, GuesthouseReview


# ==========================================
# 1. GUESTHOUSE ADMIN
# ==========================================

@admin.register(Guesthouse)
class GuesthouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'price_per_night', 'allow_room_selection', 'is_active')
    list_filter = ('is_active', 'allow_room_selection', 'city')
    search_fields = ('name', 'city', 'description')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'owner', 'description', 'city', 'is_active')
        }),
        ('Location (Coordinates)', {
            'fields': ('latitude', 'longitude'),
            'description': 'Optional: Add coordinates for future map integrations.'
        }),
        ('Pricing & Rooms', {
            'fields': ('price_per_night', 'allow_room_selection'),
            'description': 'Toggle room selection off if rooms are assigned on arrival.'
        }),
        ('Media', {
            'fields': ('main_image_url',)
        }),
    )


# ==========================================
# 2. BOOKING ADMIN
# ==========================================

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'guest', 'guesthouse', 'check_in', 'check_out', 'room_type', 'total_price', 'status', 'checked_in')
    list_filter = ('status', 'checked_in', 'room_type', 'check_in')
    search_fields = ('guest__username', 'guesthouse__name')
    
    # Custom Admin Action to Process Refunds
    actions = ['process_refund']

    @admin.action(description='Process Refund for selected bookings')
    def process_refund(self, request, queryset):
        updated_count = 0
        for booking in queryset:
            if booking.status == 'confirmed':
                booking.status = 'refunded'
                booking.save()
                updated_count += 1
        
        if updated_count > 0:
            self.message_user(
                request, 
                f'Successfully processed refunds for {updated_count} booking(s). Dates have been freed.', 
                messages.SUCCESS
            )
        else:
            self.message_user(
                request, 
                'No confirmed bookings were selected for refund.', 
                messages.WARNING
            )


# ==========================================
# 3. REVIEW ADMIN
# ==========================================

@admin.register(GuesthouseReview)
class GuesthouseReviewAdmin(admin.ModelAdmin):
    list_display = ('guesthouse', 'guest', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('guest__username', 'guesthouse__name', 'comment')