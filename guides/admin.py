import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import Guide, GuideBooking
from advisor.utils import get_whatsapp_link


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
# 2. GUIDE BOOKING ADMIN (Bulletproof & Enhanced)
# ============================================================
@admin.register(GuideBooking)
class GuideBookingAdmin(admin.ModelAdmin):
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
        'whatsapp_link',
    )
    
    list_filter = (
        'status',
        'booking_date',
        'guide__name',
        'guide__languages',
    )
    
    search_fields = (
        'guest__username',
        'guest__first_name',
        'guest__last_name',
        'guest__email',
        'guide__name',
        'guide__expertise',
    )
    
    ordering = ('-booking_date', '-id')
    readonly_fields = ('total_price', 'created_at')
    actions = ['export_to_csv', 'mark_as_confirmed', 'mark_as_declined']

    # ----------------------------------------------------------
    # Custom Methods for Better UI
    # ----------------------------------------------------------
    
    def booking_reference(self, obj):
        return f"GD-{obj.id:04d}"
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

    def guide_name(self, obj):
        return obj.guide.name
    guide_name.short_description = 'Guide'
    guide_name.admin_order_field = 'guide__name'

    def duration_display(self, obj):
        if obj.duration_hours:
            return f"{obj.duration_hours} hour{'s' if obj.duration_hours != 1 else ''}"
        return 'N/A'
    duration_display.short_description = 'Duration'

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

    def whatsapp_link(self, obj):
        """Clickable WhatsApp button for contacting the guest."""
        link = get_whatsapp_link(obj, "guide")
        if not link:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" style="background:#25D366; color:white; '
            'padding:5px 12px; border-radius:4px; text-decoration:none; '
            'font-size:12px; font-weight:bold; display:inline-block;">'
            '💬 WhatsApp</a>',
            link
        )
    whatsapp_link.short_description = 'Contact Guest'

    # ----------------------------------------------------------
    # Custom Actions
    # ----------------------------------------------------------

    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="guide_booking_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Reference', 'Guest Name', 'Email', 'Phone',
            'Guide', 'Languages', 'Booking Date', 'Start Time',
            'Duration (Hours)', 'Total Price', 'Status', 'Created At',
        ])
        
        for booking in queryset:
            guest_name = f"{booking.guest.first_name} {booking.guest.last_name}".strip() or booking.guest.username
            
            # Bulletproof phone lookup for CSV
            phone = getattr(booking, 'guest_phone', '') or getattr(booking, 'phone', '') or getattr(booking.guest, 'phone', '')
            
            writer.writerow([
                f"GD-{booking.id:04d}",
                guest_name,
                booking.guest.email,
                phone,
                booking.guide.name,
                booking.guide.languages,
                booking.booking_date.strftime('%Y-%m-%d') if booking.booking_date else 'N/A',
                booking.start_time.strftime('%H:%M') if booking.start_time else 'N/A',
                booking.duration_hours or '',
                f"₭{booking.total_price}" if booking.total_price else '',
                booking.status,
                booking.created_at.strftime('%Y-%m-%d %H:%M') if booking.created_at else 'N/A',
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