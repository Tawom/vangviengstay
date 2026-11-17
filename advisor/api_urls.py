from django.urls import path, include
from . import api_views

urlpatterns = [
    # Basic API endpoints
    path('hello/', api_views.hello_world, name='api_hello_world'),
    path('guesthouses/count/', api_views.get_guesthouse_count, name='api_guesthouse_count'),
    
    # Tour API endpoints (includes tours/api_urls.py)
    path('', include('tours.api_urls')),
]