from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # 1. Public Guide Views
    # ==========================================
    path('', views.guide_list, name='guide_list'),
    path('<int:guide_id>/', views.guide_detail, name='guide_detail'),
    path('<int:guide_id>/book/', views.create_guide_booking, name='create_guide_booking'),
    
    # ==========================================
    # 2. Booking Management (Guest)
    # ==========================================
    path('booking/<int:booking_id>/request-received/', views.guide_booking_request_received, name='guide_booking_request_received'),
    path('booking/<int:booking_id>/confirmation/', views.guide_booking_confirmation, name='guide_booking_confirmation'),
    path('booking/<int:booking_id>/cancel/', views.cancel_guide_booking, name='cancel_guide_booking'),
    
    # ==========================================
    # 3. User Dashboards
    # ==========================================
    path('dashboard/', views.guide_bookings_dashboard, name='guide_bookings_dashboard'),
    
    # ==========================================
    # 4. Owner Dashboard Actions & Management
    # ==========================================
    path('dashboard/bookings/<int:booking_id>/approve/', views.approve_guide_booking, name='approve_guide_booking'),
    path('dashboard/bookings/<int:booking_id>/decline/', views.decline_guide_booking, name='decline_guide_booking'),
    path('owner/guides/add/', views.owner_guide_add, name='owner_guide_add'),
    path('owner/guides/<int:guide_id>/edit/', views.owner_guide_edit, name='owner_guide_edit'),
]