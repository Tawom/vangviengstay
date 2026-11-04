import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import BuggyCar, BuggyCarBooking, BuggyCarReview


# ============================================================
# 1. BUGGY CAR ADMIN
# ============================================================
@admin.register(BuggyCar)
class BuggyCarAdmin(admin.ModelAdmin):
    list_display = ('name', 'size', 'owner', 'price_2_hours', 'is_active', 'created_at')
    list_filter = ('size', 'is_active', 'owner')
    search_fields = ('name', 'description', 'owner__username')
    
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


# ============================================================
# 2. BUGGY CAR BOOKING ADMIN (Enhanced with Reports & Actions)
# ============================================================
@admin.register(BuggyCarBooking)
class BuggyCarBookingAdmin(admin.ModelAdmin):
    # 1. Columns to display (enhanced with reference & badges)
    list_display = (
        'booking_reference',
        'guest_info',
        'buggy_car_name',
        'booking_date',
        'duration_hours',
        'total_price',
        'status_badge',
        'created_at',
    )
    
    # 2. Sidebar Filters (Crucial for Daily/Weekly/Monthly reports)
    list_filter = (
        'status',
        'booking_date',
        'duration_hours',
        'buggy_car__name',
        'buggy_car__size',
    )
    
    # 3. Search bar at the top
    search_fields = (
        'guest__username',
        'guest__first_name',
        'guest__last_name',
        'guest__email',
        'guest_phone',
        'buggy_car__name',
    )
    
    # 4. Default sort order (newest first)
    ordering = ('-booking_date', '-id')
    
    # 5. Read-only fields (preserved from original)
    readonly_fields = ('total_price', 'deposit_amount', 'created_at')
    
    # 6. Custom Admin Actions (Reports + Bulk Status Updates)
    actions = ['export_to_csv', 'mark_as_confirmed', 'mark_as_declined']

    # ----------------------------------------------------------
    # Custom Methods for Better UI
    # ----------------------------------------------------------
    
    def booking_reference(self, obj):
        return f"BC-{obj.id:04d}"
    booking_reference.short_description = 'Reference'
    booking_reference.admin_order_field = 'id'

    def guest_info(self, obj):
        """Shows guest name + phone in one column."""
        name = f"{obj.guest.first_name} {obj.guest.last_name}".strip() or obj.guest.username
        if obj.guest_phone:
            return format_html('{}<br><small style="color:#666;">📱 {}</small>', name, obj.guest_phone)
        return name
    guest_info.short_description = 'Guest'

    def buggy_car_name(self, obj):
        return obj.buggy_car.name
    buggy_car_name.short_description = 'Buggy Car'
    buggy_car_name.admin_order_field = 'buggy_car__name'

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
        response['Content-Disposition'] = 'attachment; filename="buggy_booking_report.csv"'
        
        writer = csv.writer(response)
        
        # CSV Header
        writer.writerow([
            'Reference', 'Guest Name', 'Email', 'Phone',
            'Buggy Car', 'Size', 'Booking Date', 'Duration (Hours)',
            'Total Price', 'Deposit', 'Status', 'Created At',
        ])
        
        # CSV Data
        for booking in queryset:
            guest_name = f"{booking.guest.first_name} {booking.guest.last_name}".strip() or booking.guest.username
            writer.writerow([
                f"BC-{booking.id:04d}",
                guest_name,
                booking.guest.email,
                booking.guest_phone or '',
                booking.buggy_car.name,
                booking.buggy_car.size,
                booking.booking_date.strftime('%Y-%m-%d') if booking.booking_date else 'N/A',
                booking.duration_hours,
                f"₭{booking.total_price}" if booking.total_price else '',
                f"₭{booking.deposit_amount}" if booking.deposit_amount else '',
                booking.status,
                booking.created_at.strftime('%Y-%m-%d %H:%M') if booking.created_at else 'N/A',
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
# 3. BUGGY CAR REVIEW ADMIN
# ============================================================
@admin.register(BuggyCarReview)
class BuggyCarReviewAdmin(admin.ModelAdmin):
    list_display = ('buggy_car', 'guest', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('buggy_car__name', 'guest__username', 'comment')