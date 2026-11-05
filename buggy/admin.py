import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import BuggyCar, BuggyCarBooking, BuggyCarReview
from advisor.utils import get_whatsapp_link


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
        ('Pickup Location', {
            'fields': ('pickup_address', 'latitude', 'longitude'),
            'description': 'Tip: Find coordinates by right-clicking on Google Maps.'
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
    list_display = (
        'booking_reference',
        'guest_info',
        'buggy_car_name',
        'booking_date',
        'duration_hours',
        'total_price',
        'status_badge',
        'created_at',
        'whatsapp_link',
    )
    
    list_filter = (
        'status',
        'booking_date',
        'duration_hours',
        'buggy_car__name',
        'buggy_car__size',
    )
    
    search_fields = (
        'guest__username',
        'guest__first_name',
        'guest__last_name',
        'guest__email',
        'buggy_car__name',
    )
    
    ordering = ('-booking_date', '-id')
    readonly_fields = ('total_price', 'deposit_amount', 'created_at')
    actions = ['export_to_csv', 'mark_as_confirmed', 'mark_as_declined']

    # ----------------------------------------------------------
    # Custom Methods for Better UI
    # ----------------------------------------------------------
    
    def booking_reference(self, obj):
        return f"BC-{obj.id:04d}"
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

    def buggy_car_name(self, obj):
        return obj.buggy_car.name
    buggy_car_name.short_description = 'Buggy Car'
    buggy_car_name.admin_order_field = 'buggy_car__name'

    def status_badge(self, obj):
        """Colorful status badge."""
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
        link = get_whatsapp_link(obj, "buggy")
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
        """Generates a CSV report of selected bookings."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="buggy_booking_report.csv"'
        
        writer = csv.writer(response)
        
        writer.writerow([
            'Reference', 'Guest Name', 'Email', 'Phone',
            'Buggy Car', 'Size', 'Booking Date', 'Duration (Hours)',
            'Total Price', 'Deposit', 'Status', 'Created At',
        ])
        
        for booking in queryset:
            guest_name = f"{booking.guest.first_name} {booking.guest.last_name}".strip() or booking.guest.username
            
            # Bulletproof phone lookup for CSV
            phone = getattr(booking, 'guest_phone', '') or getattr(booking, 'phone', '') or getattr(booking.guest, 'phone', '')
            
            writer.writerow([
                f"BC-{booking.id:04d}",
                guest_name,
                booking.guest.email,
                phone,
                booking.buggy_car.name,
                booking.buggy_car.size,
                booking.booking_date.strftime('%Y-%m-%d') if booking.booking_date else 'N/A',
                booking.duration_hours,
                f"₭{booking.total_price}" if booking.total_price else '',
                f"₭{booking.deposit_amount}" if booking.deposit_amount else '',
                booking.status,
                booking.created_at.strftime('%Y-%m-%d %H:%M') if booking.created_at else 'N/A',
            ])
        
        self.message_user(request, f'Exported {queryset.count()} booking(s) to CSV.')
        return response
    export_to_csv.short_description = "Export Selected to CSV (Report)"

    def mark_as_confirmed(self, request, queryset):
        """Bulk confirm selected bookings."""
        count = 0
        for booking in queryset.filter(status='pending'):
            booking.status = 'confirmed'
            booking.save()
            count += 1
        self.message_user(request, f'{count} booking(s) marked as Confirmed.')
    mark_as_confirmed.short_description = "Mark Selected as Confirmed"

    def mark_as_declined(self, request, queryset):
        """Bulk decline selected bookings."""
        count = 0
        for booking in queryset.filter(status='pending'):
            booking.status = 'declined'
            booking.save()
            count += 1
        self.message_user(request, f'{count} booking(s) marked as Declined.')
    mark_as_declined.short_description = "Mark Selected as Declined"


# ============================================================
# 3. BUGGY CAR REVIEW ADMIN
# ============================================================
@admin.register(BuggyCarReview)
class BuggyCarReviewAdmin(admin.ModelAdmin):
    list_display = ('buggy_car', 'guest', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('buggy_car__name', 'guest__username', 'comment')