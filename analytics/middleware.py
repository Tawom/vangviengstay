import requests
from django.core.cache import cache
from django.utils import timezone
from .models import DailyVisit, PageVisit, VisitLog


class AnalyticsMiddleware:
    """Lightweight middleware to track site visits with free geolocation."""
    
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
        if request.method != 'GET':
            return False
        
        if response.status_code != 200:
            return False
        
        path = request.path
        
        skip_prefixes = ['/admin/', '/static/', '/media/', '/api/', '/__debug__/']
        if any(path.startswith(prefix) for prefix in skip_prefixes):
            return False
        
        if path in ['/favicon.ico', '/robots.txt', '/sitemap.xml']:
            return False
        
        return True
    
    def track_visit(self, request):
        """Record the visit in the database with geolocation."""
        today = timezone.now().date()
        ip = self.get_client_ip(request)
        path = request.path
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        # Use cache to track unique visitors (24-hour expiry)
        cache_key = f"visit_{today}_{ip}"
        is_unique = not cache.get(cache_key)
        
        if is_unique:
            cache.set(cache_key, True, timeout=86400)  # 24 hours
        
        # ✅ FREE GEOLOCATION: Check cache first to avoid API rate limits
        geo_cache_key = f"geo_{ip}"
        geo_data = cache.get(geo_cache_key)
        
        if not geo_data:
            try:
                # Free, no-auth API (fields parameter keeps response tiny and fast)
                api_url = f"http://ip-api.com/json/{ip}?fields=country,city"
                response = requests.get(api_url, timeout=2)
                if response.status_code == 200:
                    geo_data = response.json()
                    # Cache location for 24 hours so we never hit rate limits for repeat visitors
                    cache.set(geo_cache_key, geo_data, timeout=86400)
                else:
                    geo_data = {'country': 'Unknown', 'city': 'Unknown'}
            except Exception:
                # Fail silently so analytics never break the user experience
                geo_data = {'country': 'Unknown', 'city': 'Unknown'}
        
        country = geo_data.get('country', 'Unknown')
        city = geo_data.get('city', 'Unknown')
        
        # ✅ Save detailed visit log with geolocation
        VisitLog.objects.create(
            path=path,
            ip_address=ip,
            user_agent=user_agent,
            is_unique=is_unique,
            country=country,
            city=city,
        )
        
        # Update daily site-wide stats (your existing code)
        daily_visit, _ = DailyVisit.objects.get_or_create(date=today)
        daily_visit.total_visits += 1
        if is_unique:
            daily_visit.unique_visitors += 1
        daily_visit.save()
        
        # Update page-specific stats (your existing code)
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