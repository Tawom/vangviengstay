from django.urls import path
from . import views

urlpatterns = [
    # Public Views
    path('', views.buggy_list, name='buggy_list'),
    path('<int:buggy_id>/', views.buggy_detail, name='buggy_detail'),
    path('<int:buggy_id>/book/', views.create_buggy_booking, name='create_buggy_booking'),
    
    # Booking Management
    path('booking/<int:booking_id>/request-received/', views.buggy_booking_request_received, name='buggy_booking_request_received'),
    path('booking/<int:booking_id>/confirmation/', views.buggy_booking_confirmation, name='buggy_booking_confirmation'),
    path('booking/<int:booking_id>/cancel/', views.cancel_buggy_booking, name='cancel_buggy_booking'),
    
    # User Dashboard
    path('dashboard/', views.buggy_bookings_dashboard, name='buggy_bookings_dashboard'),
    
    # Owner Actions
    path('dashboard/bookings/<int:booking_id>/approve/', views.approve_buggy_booking, name='approve_buggy_booking'),
    path('dashboard/bookings/<int:booking_id>/decline/', views.decline_buggy_booking, name='decline_buggy_booking'),
    path('owner/buggy/add/', views.owner_buggy_add, name='owner_buggy_add'),
    path('owner/buggy/<int:buggy_id>/edit/', views.owner_buggy_edit, name='owner_buggy_edit'),
]