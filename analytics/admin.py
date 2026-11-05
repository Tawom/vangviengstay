from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import timedelta
from .models import DailyVisit, PageVisit


@admin.register(DailyVisit)
class DailyVisitAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_visits', 'unique_visitors')
    list_filter = ('date',)
    readonly_fields = ('date', 'total_visits', 'unique_visitors')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = ('date', 'path', 'visit_count', 'unique_visitors')
    list_filter = ('date', 'path')
    readonly_fields = ('date', 'path', 'visit_count', 'unique_visitors')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


class AnalyticsAdminSite(admin.AdminSite):
    """Custom admin site with analytics dashboard."""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('analytics/', self.admin_view(self.analytics_view), name='analytics_dashboard'),
        ]
        return custom_urls + urls
    
    def analytics_view(self, request):
        """Custom analytics dashboard view."""
        today = timezone.now().date()
        
        # Today's stats
        today_stats = DailyVisit.objects.filter(date=today).first()
        
        # Last 7 days
        last_7_days = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            stats = DailyVisit.objects.filter(date=date).first()
            last_7_days.append({
                'date': date.strftime('%a'),
                'visits': stats.total_visits if stats else 0,
                'unique': stats.unique_visitors if stats else 0,
            })
        
        # Last 30 days total
        thirty_days_ago = today - timedelta(days=30)
        monthly_stats = DailyVisit.objects.filter(
            date__gte=thirty_days_ago
        ).aggregate(
            total_visits=Sum('total_visits'),
            total_unique=Sum('unique_visitors')
        )
        
        # Top pages (last 7 days)
        seven_days_ago = today - timedelta(days=7)
        top_pages = PageVisit.objects.filter(
            date__gte=seven_days_ago
        ).values('path').annotate(
            total_visits=Sum('visit_count')
        ).order_by('-total_visits')[:10]
        
        context = {
            'title': 'Site Analytics',
            'today_stats': today_stats,
            'last_7_days': last_7_days,
            'monthly_stats': monthly_stats,
            'top_pages': top_pages,
        }
        
        return render(request, 'admin/analytics_dashboard.html', context)


# Register the custom admin site
analytics_admin_site = AnalyticsAdminSite(name='analytics_admin')
analytics_admin_site.register(DailyVisit, DailyVisitAdmin)
analytics_admin_site.register(PageVisit, PageVisitAdmin)