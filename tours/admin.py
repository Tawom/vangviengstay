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
# TOUR BOOKING ADMIN (Merged + Enhanced with Reports)
# ============================================================
@admin.register(TourBooking)
class TourBookingAdmin(admin.ModelAdmin):
    # 1. Columns to display (merged from both versions)
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
    
    # 2. Sidebar Filters (Crucial for Daily/Weekly/Monthly reports)
    list_filter = (
        'status',
        'attended',
        'pickup_option',
        'booking_date',
        'tour__name',
        'tour__operator_name',
    )
    
    # 3. Search bar at the top
    search_fields = (
        'guest__username',
        'guest__first_name',
        'guest__last_name',
        'guest__email',
        'guest_phone',
        'tour__name',
        'tour__operator_name',
        'pickup_location',
    )
    
    # 4. Default sort order (newest first)
    ordering = ('-booking_date', '-id')
    
    # 5. Custom Admin Actions (The "Report" Generator)
    actions = ['export_to_csv', 'mark_as_confirmed', 'mark_as_declined']

    # ----------------------------------------------------------
    # Custom Methods for Better UI
    # ----------------------------------------------------------
    
    def booking_reference(self, obj):
        return f"TV-{obj.id:04d}"
    booking_reference.short_description = 'Reference'
    booking_reference.admin_order_field = 'id'

    def guest_info(self, obj):
        """Shows guest name + phone in one column."""
        name = f"{obj.guest.first_name} {obj.guest.last_name}".strip() or obj.guest.username
        if obj.guest_phone:
            return format_html('{}<br><small style="color:#666;">📱 {}</small>', name, obj.guest_phone)
        return name
    guest_info.short_description = 'Guest'

    def tour_name(self, obj):
        return obj.tour.name
    tour_name.short_description = 'Tour'
    tour_name.admin_order_field = 'tour__name'

    def status_badge(self, obj):
        """Colorful status badge."""
        colors = {
            'pending': '#ffa500',    # Orange
            'confirmed': '#28a745',  # Green
            'declined': '#dc3545',   # Red
            'cancelled': '#6c757d',  # Gray
            'completed': '#17a2b8',  # Blue
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
    # Custom Actions
    # ----------------------------------------------------------

    def export_to_csv(self, request, queryset):
        """Generates a CSV report of selected bookings."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tour_booking_report.csv"'
        
        writer = csv.writer(response)
        
        # CSV Header
        writer.writerow([
            'Reference', 'Guest Name', 'Email', 'Phone',
            'Tour', 'Operator', 'Booking Date', 'Pickup Option',
            'Pickup Location', 'Total Price', 'Status', 'Attended',
        ])
        
        # CSV Data
        for booking in queryset:
            guest_name = f"{booking.guest.first_name} {booking.guest.last_name}".strip() or booking.guest.username
            writer.writerow([
                f"TV-{booking.id:04d}",
                guest_name,
                booking.guest.email,
                booking.guest_phone or '',
                booking.tour.name,
                booking.tour.operator_name,
                booking.booking_date.strftime('%Y-%m-%d') if booking.booking_date else 'N/A',
                booking.pickup_option or '',
                booking.pickup_location or '',
                f"${booking.total_price}" if booking.total_price else '',
                booking.status,
                'Yes' if booking.attended else 'No',
            ])
        
        self.message_user(request, f'📥 Exported {queryset.count()} booking(s) to CSV.')
        return response
    export_to_csv.short_description = "📥 Export Selected to CSV (Report)"

    def mark_as_confirmed(self, request, queryset):
        """Bulk confirm selected bookings."""
        count = 0
        for booking in queryset.filter(status='pending'):
            booking.status = 'confirmed'
            booking.save()
            count += 1
        self.message_user(request, f'✅ {count} booking(s) marked as Confirmed.')
    mark_as_confirmed.short_description = "✅ Mark Selected as Confirmed"

    def mark_as_declined(self, request, queryset):
        """Bulk decline selected bookings."""
        count = 0
        for booking in queryset.filter(status='pending'):
            booking.status = 'declined'
            booking.save()
            count += 1
        self.message_user(request, f'❌ {count} booking(s) marked as Declined.')
    mark_as_declined.short_description = "❌ Mark Selected as Declined"


# ============================================================
# TOUR REVIEW ADMIN
# ============================================================
@admin.register(TourReview)
class TourReviewAdmin(admin.ModelAdmin):
    list_display = ('tour', 'guest', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('guest__username', 'tour__name', 'tour__operator_name', 'comment')