# advisor/middleware.py
import os
from django.shortcuts import render
from django.conf import settings

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Path to the flag file. If this file exists, maintenance mode is ON.
        self.maintenance_file = os.path.join(settings.BASE_DIR, 'maintenance.txt')

    def __call__(self, request):
        # If the file exists AND the user is NOT a staff member, show maintenance page
        if os.path.exists(self.maintenance_file) and not request.user.is_staff:
            # Return a 503 Service Unavailable status (Crucial for SEO!)
            response = render(request, 'maintenance.html', status=503)
            # Tell browsers and search engines to retry later
            response['Retry-After'] = '3600' # Retry in 1 hour
            return response
            
        return self.get_response(request)