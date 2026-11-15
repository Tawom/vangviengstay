from django.contrib import admin
from .models import Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'status', 'customer_email_sent', 'admin_email_sent', 'created_at')
    list_filter = ('status', 'subject', 'created_at')
    search_fields = ('name', 'email', 'message', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'customer_email_sent', 'admin_email_sent')
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'subject')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status & Tracking', {
            'fields': ('status', 'customer_email_sent', 'admin_email_sent', 'created_at', 'updated_at')
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_responded', 'mark_as_closed']
    
    def mark_as_read(self, request, queryset):
        queryset.update(status='read')
    mark_as_read.short_description = "Mark selected as Read"
    
    def mark_as_responded(self, request, queryset):
        queryset.update(status='responded')
    mark_as_responded.short_description = "Mark selected as Responded"
    
    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')
    mark_as_closed.short_description = "Mark selected as Closed"