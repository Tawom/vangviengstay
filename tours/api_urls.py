from django.urls import path
from . import api_views

urlpatterns = [
    path('tours/', api_views.tour_list, name='api_tour_list'),
    path('tours/<int:pk>/', api_views.tour_detail, name='api_tour_detail'),
]