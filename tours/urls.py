from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # 1. Public Tour Views
    # ==========================================
    path('', views.tour_list, name='tour_list'),
    path('<int:tour_id>/', views.tour_detail, name='tour_detail'),
    path('<int:tour_id>/book/', views.create_tour_booking, name='create_tour_booking'),
    
    # ==========================================
    # 2. Booking Management (Guest)
    # ==========================================
    path('booking/<int:booking_id>/request-received/', views.tour_booking_request_received, name='tour_booking_request_received'),
    path('booking/<int:booking_id>/confirmation/', views.tour_booking_confirmation, name='tour_booking_confirmation'),
    path('booking/<int:booking_id>/cancel/', views.cancel_tour_booking, name='cancel_tour_booking'),
    
    # ==========================================
    # 3. User Dashboards
    # ==========================================
    path('dashboard/', views.tour_bookings_dashboard, name='tour_bookings_dashboard'),
    
    # ==========================================
    # 4. Owner Dashboard Actions & Management
    # ==========================================
    path('dashboard/bookings/<int:booking_id>/approve/', views.approve_tour_booking, name='approve_tour_booking'),
    path('dashboard/bookings/<int:booking_id>/decline/', views.decline_tour_booking, name='decline_tour_booking'),
    path('owner/tours/add/', views.owner_tour_add, name='owner_tour_add'),
    path('owner/tours/<int:tour_id>/edit/', views.owner_tour_edit, name='owner_tour_edit'),
    
    # ==========================================
    # 5. Reviews
    # ==========================================
    path('booking/<int:booking_id>/review/', views.submit_tour_review, name='submit_tour_review'),
    path('booking/<int:booking_id>/review/edit/', views.edit_tour_review, name='edit_tour_review'),
    path('booking/<int:booking_id>/review/delete/', views.delete_tour_review, name='delete_tour_review'),
]