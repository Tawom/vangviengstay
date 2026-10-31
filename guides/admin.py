from django.contrib import admin
from .models import Guide, GuideBooking

@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ('name', 'languages', 'hourly_rate', 'is_active', 'owner')
    list_filter = ('is_active', 'languages')
    search_fields = ('name', 'bio', 'expertise')

@admin.register(GuideBooking)
class GuideBookingAdmin(admin.ModelAdmin):
    list_display = ('guide', 'guest', 'booking_date', 'start_time', 'duration_hours', 'total_price', 'status')
    list_filter = ('status', 'booking_date')