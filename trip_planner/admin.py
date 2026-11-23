from django.contrib import admin
from .models import TripPlan


@admin.register(TripPlan)
class TripPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'travel_date_start', 'group_size', 'budget', 'status', 'created_at')
    list_filter = ('status', 'budget', 'created_at')
    search_fields = ('name', 'email', 'whatsapp')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)