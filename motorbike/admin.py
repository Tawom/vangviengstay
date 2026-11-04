import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import Motorbike, MotorbikeBooking, MotorbikeReview


# ============================================================
# 1. MOTORBIKE ADMIN
# ============================================================
@admin.register(Motorbike)
class MotorbikeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'owner', 'price_per_day', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'owner')
    search_fields = ('name', 'description', 'owner__username')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'owner', 'category', 'engine_cc')
        }),
        ('Pricing', {
            'fields': ('price_per_day', 'deposit_amount')
        }),
        ('Description & Media', {
            'fields': ('description', 'image_url'),
            'classes': ('collapse',)
        }),
        ('📍 Pickup Location', {
            'fields': ('pickup_address', 'latitude', 'longitude'),
            'description': '💡 Tip: Find coordinates by right-clicking on Google Maps and copying the numbers.'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


# ============================================================
# 2. MOTORBIKE BOOKING ADMIN (Enhanced with Reports & Actions)
# ============================================================
@admin.register(MotorbikeBooking)
class MotorbikeBookingAdmin(admin.ModelAdmin):
    # 1. Columns to display (enhanced with reference & badges)
    list_display = (
        'booking_reference',
        'guest_info',
        'motorbike_name',
        'start_date',
        'end_date',
        'duration_display',
        'total_price',
        'status_badge',
        'created_at',
    )
    
    # 2. Sidebar Filters (Crucial for Daily/Weekly/Monthly reports)
    list_filter = (
        'status',
        'start_date',
        'motorbike__name',
        'motorbike__category',
    )
    
    # 3. Search bar at the top
    search_fields = (
        'guest__username',
        'guest__first_name',
        'guest__last_name',
        'guest__email',
        'guest_phone',
        'motorbike__name',
        'motorbike__category',
    )
    
    # 4. Default sort order (newest first)
    ordering = ('-start_date', '-id')
    
    # 5. Read-only fields (preserved from original)
    readonly_fields = ('total_price', 'deposit_amount', 'created_at')
    
    # 6. Custom Admin Actions (Reports + Bulk Status Updates)
    actions = ['export_to_csv', 'mark_as_confirmed', 'mark_as_declined']

    # ----------------------------------------------------------
    # Custom Methods for Better UI
    # ----------------------------------------------------------
    
    def booking_reference(self, obj):
        return f"MB-{obj.id:04d}"
    booking_reference.short_description = 'Reference'
    booking_reference.admin_order_field = 'id'

    def guest_info(self, obj):
        """Shows guest name + phone in one column."""
        name = f"{obj.guest.first_name} {obj.guest.last_name}".strip() or obj.guest.username
        if obj.guest_phone:
            return format_html('{}<br><small style="color:#666;">📱 {}</small>', name, obj.guest_phone)
        return name
    guest_info.short_description = 'Guest'

    def motorbike_name(self, obj):
        return obj.motorbike.name
    motorbike_name.short_description = 'Motorbike'
    motorbike_name.admin_order_field = 'motorbike__name'

    def duration_display(self, obj):
        """Shows rental duration in days."""
        if obj.start_date and obj.end_date:
            days = (obj.end_date - obj.start_date).days
            return f"{days} day{'s' if days != 1 else ''}"
        return 'N/A'
    duration_display.short_description = 'Duration'

    def status_badge(self, obj):
        """Colorful status badge."""
        colors = {
            'pending': '#ffa500',    # Orange
            'confirmed': '#28a745',  # Green
            'declined': '#dc3545',   # Red
            'cancelled': '#6c757d',  # Gray
            'completed': '#17a2b8',  # Blue
            'picked_up': '#6f42c1',  # Purple
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
        response['Content-Disposition'] = 'attachment; filename="motorbike_booking_report.csv"'
        
        writer = csv.writer(response)
        
        # CSV Header
        writer.writerow([
            'Reference', 'Guest Name', 'Email', 'Phone',
            'Motorbike', 'Category', 'Start Date', 'End Date',
            'Duration (Days)', 'Total Price', 'Deposit', 'Status', 'Created At',
        ])
        
        # CSV Data
        for booking in queryset:
            guest_name = f"{booking.guest.first_name} {booking.guest.last_name}".strip() or booking.guest.username
            duration = (booking.end_date - booking.start_date).days if booking.start_date and booking.end_date else 0
            writer.writerow([
                f"MB-{booking.id:04d}",
                guest_name,
                booking.guest.email,
                booking.guest_phone or '',
                booking.motorbike.name,
                booking.motorbike.category,
                booking.start_date.strftime('%Y-%m-%d') if booking.start_date else 'N/A',
                booking.end_date.strftime('%Y-%m-%d') if booking.end_date else 'N/A',
                duration,
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
# 3. MOTORBIKE REVIEW ADMIN
# ============================================================
@admin.register(MotorbikeReview)
class MotorbikeReviewAdmin(admin.ModelAdmin):
    list_display = ('motorbike', 'guest', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('motorbike__name', 'guest__username', 'comment')
    readonly_fields = ('booking', 'motorbike', 'guest', 'created_at')