from django.core.cache import cache
from django.utils import timezone
from .models import DailyVisit, PageVisit


class AnalyticsMiddleware:
    """Lightweight middleware to track site visits."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only track successful GET requests to public pages
        if self.should_track(request, response):
            self.track_visit(request)
        
        return response
    
    def should_track(self, request, response):
        """Determine if this request should be tracked."""
        # Only track GET requests
        if request.method != 'GET':
            return False
        
        # Only track successful responses
        if response.status_code != 200:
            return False
        
        path = request.path
        
        # Skip admin, static, media, and API routes
        skip_prefixes = ['/admin/', '/static/', '/media/', '/api/', '/__debug__/']
        if any(path.startswith(prefix) for prefix in skip_prefixes):
            return False
        
        # Skip favicon and robots.txt
        if path in ['/favicon.ico', '/robots.txt', '/sitemap.xml']:
            return False
        
        return True
    
    def track_visit(self, request):
        """Record the visit in the database."""
        today = timezone.now().date()
        ip = self.get_client_ip(request)
        path = request.path
        
        # Use cache to track unique visitors (24-hour expiry)
        cache_key = f"visit_{today}_{ip}"
        is_unique = not cache.get(cache_key)
        
        if is_unique:
            cache.set(cache_key, True, timeout=86400)  # 24 hours
        
        # Update daily site-wide stats
        daily_visit, _ = DailyVisit.objects.get_or_create(date=today)
        daily_visit.total_visits += 1
        if is_unique:
            daily_visit.unique_visitors += 1
        daily_visit.save()
        
        # Update page-specific stats
        page_visit, _ = PageVisit.objects.get_or_create(
            date=today,
            path=path
        )
        page_visit.visit_count += 1
        if is_unique:
            page_visit.unique_visitors += 1
        page_visit.save()
    
    def get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip