import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import Guide, GuideBooking


# ============================================================
# 1. GUIDE ADMIN
# ============================================================
@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ('name', 'languages', 'hourly_rate', 'is_active', 'owner')
    list_filter = ('is_active', 'languages')
    search_fields = ('name', 'bio', 'expertise')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'owner', 'languages', 'expertise')
        }),
        ('Pricing', {
            'fields': ('hourly_rate',)
        }),
        ('Bio & Description', {
            'fields': ('bio',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


# ============================================================
# 2. GUIDE BOOKING ADMIN (Enhanced with Reports & Actions)
# ============================================================
@admin.register(GuideBooking)
class GuideBookingAdmin(admin.ModelAdmin):
    # 1. Columns to display (enhanced with reference & badges)
    list_display = (
        'booking_reference',
        'guest_info',
        'guide_name',
        'booking_date',
        'start_time',
        'duration_display',
        'total_price',
        'status_badge',
        'created_at',
    )
    
    # 2. Sidebar Filters (Crucial for Daily/Weekly/Monthly reports)
    list_filter = (
        'status',
        'booking_date',
        'guide__name',
        'guide__languages',
    )
    
    # 3. Search bar at the top
    search_fields = (
        'guest__username',
        'guest__first_name',
        'guest__last_name',
        'guest__email',
        'guest_phone',
        'guide__name',
        'guide__expertise',
    )
    
    # 4. Default sort order (newest first)
    ordering = ('-booking_date', '-id')
    
    # 5. Read-only fields
    readonly_fields = ('total_price', 'created_at')
    
    # 6. Custom Admin Actions (Reports + Bulk Status Updates)
    actions = ['export_to_csv', 'mark_as_confirmed', 'mark_as_declined']

    # ----------------------------------------------------------
    # Custom Methods for Better UI
    # ----------------------------------------------------------
    
    def booking_reference(self, obj):
        return f"GD-{obj.id:04d}"
    booking_reference.short_description = 'Reference'
    booking_reference.admin_order_field = 'id'

    def guest_info(self, obj):
        """Shows guest name + phone in one column."""
        name = f"{obj.guest.first_name} {obj.guest.last_name}".strip() or obj.guest.username
        if obj.guest_phone:
            return format_html('{}<br><small style="color:#666;">📱 {}</small>', name, obj.guest_phone)
        return name
    guest_info.short_description = 'Guest'

    def guide_name(self, obj):
        return obj.guide.name
    guide_name.short_description = 'Guide'
    guide_name.admin_order_field = 'guide__name'

    def duration_display(self, obj):
        """Shows booking duration in hours."""
        if obj.duration_hours:
            return f"{obj.duration_hours} hour{'s' if obj.duration_hours != 1 else ''}"
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
        response['Content-Disposition'] = 'attachment; filename="guide_booking_report.csv"'
        
        writer = csv.writer(response)
        
        # CSV Header
        writer.writerow([
            'Reference', 'Guest Name', 'Email', 'Phone',
            'Guide', 'Languages', 'Booking Date', 'Start Time',
            'Duration (Hours)', 'Total Price', 'Status', 'Created At',
        ])
        
        # CSV Data
        for booking in queryset:
            guest_name = f"{booking.guest.first_name} {booking.guest.last_name}".strip() or booking.guest.username
            writer.writerow([
                f"GD-{booking.id:04d}",
                guest_name,
                booking.guest.email,
                booking.guest_phone or '',
                booking.guide.name,
                booking.guide.languages,
                booking.booking_date.strftime('%Y-%m-%d') if booking.booking_date else 'N/A',
                booking.start_time.strftime('%H:%M') if booking.start_time else 'N/A',
                booking.duration_hours or '',
                f"₭{booking.total_price}" if booking.total_price else '',
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