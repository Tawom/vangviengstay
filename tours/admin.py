import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import Tour, TourBooking, TourReview


# ============================================================
# TOUR ADMIN
# ============================================================
@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ('name', 'operator_name', 'price_per_person', 'duration_hours', 'max_capacity', 'is_active')
    list_filter = ('is_active', 'duration_hours')
    search_fields = ('name', 'operator_name', 'description')
    
    fieldsets = (
        ('Basic Information', {
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


# ============================================================
# TOUR BOOKING ADMIN (Clean, Reliable & Bulletproof)
# ============================================================
@admin.register(TourBooking)
class TourBookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_reference',
        'guest_info',
        'tour_name',
        'booking_date',
        'pickup_option',
        'total_price',
        'status_badge',
        'attended',
    )
    
    list_filter = (
        'status',
        'attended',
        'pickup_option',
        'booking_date',
        'tour__name',
        'tour__operator_name',
    )
    
    search_fields = (
        'guest__username',
        'guest__first_name',
        'guest__last_name',
        'guest__email',
        'tour__name',
        'tour__operator_name',
        'pickup_location',
        # Removed 'guest_phone' from search_fields to prevent FieldError if it's not a direct model field
    )
    
    ordering = ('-booking_date', '-id')
    
    # ✅ THIS IS THE KEY LINE - Must be present!
    actions = ['export_to_csv', 'mark_as_confirmed', 'mark_as_declined']

    # ----------------------------------------------------------
    # Custom Display Methods
    # ----------------------------------------------------------
    
    def booking_reference(self, obj):
        return f"TV-{obj.id:04d}"
    booking_reference.short_description = 'Reference'
    booking_reference.admin_order_field = 'id'

    def guest_info(self, obj):
        """Bulletproof guest info display."""
        name = f"{obj.guest.first_name} {obj.guest.last_name}".strip() or obj.guest.username
        
        # Safely check for phone on Booking, then on Guest model
        phone = getattr(obj, 'guest_phone', None) or getattr(obj, 'phone', None) or getattr(obj.guest, 'phone', None)
        
        if phone:
            return format_html('{}<br><small style="color:#666;">📱 {}</small>', name, phone)
        return name
    guest_info.short_description = 'Guest'

    def tour_name(self, obj):
        return obj.tour.name
    tour_name.short_description = 'Tour'
    tour_name.admin_order_field = 'tour__name'

    def status_badge(self, obj):
        colors = {
            'pending': '#ffa500',
            'confirmed': '#28a745',
            'declined': '#dc3545',
            'cancelled': '#6c757d',
            'completed': '#17a2b8',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status.upper()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    # ----------------------------------------------------------
    # ✅ ACTION METHODS (Using .short_description attributes)
    # ----------------------------------------------------------

    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tour_booking_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Reference', 'Guest Name', 'Email', 'Phone',
            'Tour', 'Operator', 'Booking Date', 'Pickup Option',
            'Pickup Location', 'Total Price', 'Status', 'Attended',
        ])
        
        for booking in queryset:
            guest_name = f"{booking.guest.first_name} {booking.guest.last_name}".strip() or booking.guest.username
            
            # Bulletproof phone lookup for CSV
            phone = getattr(booking, 'guest_phone', '') or getattr(booking, 'phone', '') or getattr(booking.guest, 'phone', '')
            
            writer.writerow([
                f"TV-{booking.id:04d}",
                guest_name,
                booking.guest.email,
                phone,
                booking.tour.name,
                booking.tour.operator_name,
                booking.booking_date.strftime('%Y-%m-%d') if booking.booking_date else 'N/A',
                booking.pickup_option or '',
                booking.pickup_location or '',
                f"${booking.total_price}" if booking.total_price else '',
                booking.status,
                'Yes' if booking.attended else 'No',
            ])
        
        self.message_user(request, f'Exported {queryset.count()} booking(s) to CSV.')
        return response
    export_to_csv.short_description = "Export Selected to CSV (Report)"

    def mark_as_confirmed(self, request, queryset):
        count = 0
        for booking in queryset.filter(status='pending'):
            booking.status = 'confirmed'
            booking.save()
            count += 1
        self.message_user(request, f'{count} booking(s) marked as Confirmed.')
    mark_as_confirmed.short_description = "Mark Selected as Confirmed"

    def mark_as_declined(self, request, queryset):
        count = 0
        for booking in queryset.filter(status='pending'):
            booking.status = 'declined'
            booking.save()
            count += 1
        self.message_user(request, f'{count} booking(s) marked as Declined.')
    mark_as_declined.short_description = "Mark Selected as Declined"


# ============================================================
# TOUR REVIEW ADMIN
# ============================================================
@admin.register(TourReview)
class TourReviewAdmin(admin.ModelAdmin):
    list_display = ('tour', 'guest', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('guest__username', 'tour__name', 'tour__operator_name', 'comment')