import csv
from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse
from django.utils.html import format_html
from .models import Guesthouse, Booking, GuesthouseReview
from advisor.utils import get_whatsapp_link


# ============================================================
# 1. GUESTHOUSE ADMIN
# ============================================================
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


# ============================================================
# 2. BOOKING ADMIN (Enhanced with Reports & Actions)
# ============================================================
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_reference',
        'guest_info',
        'guesthouse_name',
        'check_in',
        'check_out',
        'room_type',
        'total_price',
        'status_badge',
        'checked_in',
        'whatsapp_link',
    )
    
    list_filter = (
        'status',
        'checked_in',
        'room_type',
        'check_in',
        'guesthouse__name',
        'guesthouse__city',
    )
    
    search_fields = (
        'guest__username',
        'guest__first_name',
        'guest__last_name',
        'guest__email',
        'guesthouse__name',
        'guesthouse__city',
    )
    
    ordering = ('-check_in', '-id')
    
    actions = ['export_to_csv', 'mark_as_confirmed', 'mark_as_declined', 'process_refund']

    # ----------------------------------------------------------
    # Custom Methods for Better UI
    # ----------------------------------------------------------
    
    def booking_reference(self, obj):
        return f"VV-{obj.id:04d}"
    booking_reference.short_description = 'Reference'
    booking_reference.admin_order_field = 'id'

    def guest_info(self, obj):
        """Shows guest name + phone in one column (Bulletproof lookup)."""
        name = f"{obj.guest.first_name} {obj.guest.last_name}".strip() or obj.guest.username
        
        # Safely check for phone on Booking, then on Guest model
        phone = getattr(obj, 'guest_phone', None) or getattr(obj, 'phone', None) or getattr(obj.guest, 'phone', None)
        
        if phone:
            return format_html('{}<br><small style="color:#666;">📱 {}</small>', name, phone)
        return name
    guest_info.short_description = 'Guest'

    def guesthouse_name(self, obj):
        return obj.guesthouse.name
    guesthouse_name.short_description = 'Guesthouse'
    guesthouse_name.admin_order_field = 'guesthouse__name'

    def status_badge(self, obj):
        """Colorful status badge."""
        colors = {
            'pending': '#ffa500',
            'confirmed': '#28a745',
            'declined': '#dc3545',
            'cancelled': '#6c757d',
            'refunded': '#17a2b8',
            'checked_out': '#6f42c1',
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
        link = get_whatsapp_link(obj, "guesthouse")
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
        response['Content-Disposition'] = 'attachment; filename="guesthouse_booking_report.csv"'
        
        writer = csv.writer(response)
        
        writer.writerow([
            'Reference', 'Guest Name', 'Email', 'Phone',
            'Guesthouse', 'City', 'Check-in', 'Check-out',
            'Room Type', 'Total Price', 'Status', 'Checked In',
        ])
        
        for booking in queryset:
            guest_name = f"{booking.guest.first_name} {booking.guest.last_name}".strip() or booking.guest.username
            
            # Bulletproof phone lookup for CSV
            phone = getattr(booking, 'guest_phone', '') or getattr(booking, 'phone', '') or getattr(booking.guest, 'phone', '')
            
            writer.writerow([
                f"VV-{booking.id:04d}",
                guest_name,
                booking.guest.email,
                phone,
                booking.guesthouse.name,
                booking.guesthouse.city,
                booking.check_in.strftime('%Y-%m-%d') if booking.check_in else 'N/A',
                booking.check_out.strftime('%Y-%m-%d') if booking.check_out else 'N/A',
                booking.room_type or '',
                f"${booking.total_price}" if booking.total_price else '',
                booking.status,
                'Yes' if booking.checked_in else 'No',
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
    process_refund.short_description = "Process Refund for selected bookings"


# ============================================================
# 3. REVIEW ADMIN
# ============================================================
@admin.register(GuesthouseReview)
class GuesthouseReviewAdmin(admin.ModelAdmin):
    list_display = ('guesthouse', 'guest', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('guest__username', 'guesthouse__name', 'comment')