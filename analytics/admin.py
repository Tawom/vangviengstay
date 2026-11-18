from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import DailyVisit, PageVisit, VisitLog


# ==========================================
# 1. DAILY VISIT ADMIN
# ==========================================
@admin.register(DailyVisit)
class DailyVisitAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_visits', 'unique_visitors')
    list_filter = ('date',)
    readonly_fields = ('date', 'total_visits', 'unique_visitors')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ==========================================
# 2. PAGE VISIT ADMIN
# ==========================================
@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = ('date', 'path', 'visit_count', 'unique_visitors')
    list_filter = ('date', 'path')
    readonly_fields = ('date', 'path', 'visit_count', 'unique_visitors')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ==========================================
# 3. VISIT LOG ADMIN (With Geolocation!)
# ==========================================
@admin.register(VisitLog)
class VisitLogAdmin(admin.ModelAdmin):
    list_display = ('path', 'ip_address', 'location_info', 'timestamp', 'is_unique', 'device_info')
    list_filter = ('timestamp', 'country', 'is_unique')
    search_fields = ('path', 'ip_address', 'user_agent', 'country', 'city')
    readonly_fields = ('path', 'ip_address', 'user_agent', 'timestamp', 'is_unique', 'country', 'city')
    date_hierarchy = 'timestamp'

    def location_info(self, obj):
        """Combine city and country for a clean display."""
        if obj.country and obj.country != 'Unknown':
            city_str = f", {obj.city}" if obj.city and obj.city != 'Unknown' else ""
            return f"🌍 {obj.country}{city_str}"
        return "🌐 Unknown"
    location_info.short_description = 'Location'

    def device_info(self, obj):
        """Show a readable device type from the user agent."""
        ua = obj.user_agent or 'Unknown'
        if 'iPhone' in ua or 'iPad' in ua:
            return '📱 iOS'
        elif 'Android' in ua:
            return '📱 Android'
        elif 'Windows' in ua:
            return '💻 Windows'
        elif 'Macintosh' in ua or 'Mac OS' in ua:
            return '💻 Mac'
        elif 'bot' in ua.lower() or 'crawler' in ua.lower() or 'spider' in ua.lower():
            return '🤖 Search Bot'
        return '🌐 Other'
    device_info.short_description = 'Device'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ==========================================
# 4. CUSTOM ANALYTICS DASHBOARD
# ==========================================
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
        
        # Recent detailed visit logs (last 20)
        recent_visits = VisitLog.objects.all()[:20]
        
        # Device breakdown (last 7 days)
        seven_days_ago_visits = VisitLog.objects.filter(timestamp__date__gte=seven_days_ago)
        
        def get_device_type(ua):
            ua = ua or ''
            if 'iPhone' in ua or 'iPad' in ua:
                return 'iOS'
            elif 'Android' in ua:
                return 'Android'
            elif 'Windows' in ua:
                return 'Windows'
            elif 'Macintosh' in ua or 'Mac OS' in ua:
                return 'Mac'
            elif 'bot' in ua.lower() or 'crawler' in ua.lower() or 'spider' in ua.lower():
                return 'Bot'
            return 'Other'
        
        # Count devices manually (since user_agent is a TextField)
        device_counts = {'iOS': 0, 'Android': 0, 'Windows': 0, 'Mac': 0, 'Bot': 0, 'Other': 0}
        for visit in seven_days_ago_visits.values_list('user_agent', flat=True):
            device_type = get_device_type(visit)
            device_counts[device_type] = device_counts.get(device_type, 0) + 1
        
        # Unique IPs in last 7 days
        unique_ips_7d = seven_days_ago_visits.values('ip_address').distinct().count()
        
        # ✅ NEW: Country breakdown (last 7 days)
        country_counts = {}
        for visit in seven_days_ago_visits.values('country').annotate(count=Count('id')).order_by('-count'):
            if visit['country'] and visit['country'] != 'Unknown':
                country_counts[visit['country']] = visit['count']
        
        # Take top 10 countries
        top_countries = dict(list(country_counts.items())[:10])
        
        context = {
            'title': 'Site Analytics',
            'today_stats': today_stats,
            'last_7_days': last_7_days,
            'monthly_stats': monthly_stats,
            'top_pages': top_pages,
            'recent_visits': recent_visits,
            'device_counts': device_counts,
            'unique_ips_7d': unique_ips_7d,
            'top_countries': top_countries,  # ✅ NEW
        }
        
        return render(request, 'admin/analytics_dashboard.html', context)


# Register the custom admin site
analytics_admin_site = AnalyticsAdminSite(name='analytics_admin')
analytics_admin_site.register(DailyVisit, DailyVisitAdmin)
analytics_admin_site.register(PageVisit, PageVisitAdmin)
analytics_admin_site.register(VisitLog, VisitLogAdmin)