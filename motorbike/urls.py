from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # 1. Public Motorbike Views
    # ==========================================
    path('', views.motorbike_list, name='motorbike_list'),
    path('<int:motorbike_id>/', views.motorbike_detail, name='motorbike_detail'),
    path('<int:motorbike_id>/book/', views.create_motorbike_booking, name='create_motorbike_booking'),
    
    # ==========================================
    # 2. Booking Management (Guest)
    # ==========================================
    path('booking/<int:booking_id>/request-received/', views.motorbike_booking_request_received, name='motorbike_booking_request_received'),
    path('booking/<int:booking_id>/confirmation/', views.motorbike_booking_confirmation, name='motorbike_booking_confirmation'),
    path('booking/<int:booking_id>/cancel/', views.cancel_motorbike_booking, name='cancel_motorbike_booking'),
    
    # ==========================================
    # 3. User Dashboards
    # ==========================================
    path('dashboard/', views.motorbike_bookings_dashboard, name='motorbike_bookings_dashboard'),
    
    # ==========================================
    # 4. Owner Dashboard Actions & Management
    # ==========================================
    path('dashboard/bookings/<int:booking_id>/approve/', views.approve_motorbike_booking, name='approve_motorbike_booking'),
    path('dashboard/bookings/<int:booking_id>/decline/', views.decline_motorbike_booking, name='decline_motorbike_booking'),
    path('owner/motorbikes/<int:motorbike_id>/bookings/', views.owner_motorbike_bookings, name='owner_motorbike_bookings'),
    path('owner/motorbikes/add/', views.owner_motorbike_add, name='owner_motorbike_add'),
    path('owner/motorbikes/<int:motorbike_id>/edit/', views.owner_motorbike_edit, name='owner_motorbike_edit'),
    
    # ==========================================
    # 5. Reviews
    # ==========================================
    path('booking/<int:booking_id>/review/', views.submit_motorbike_review, name='submit_motorbike_review'),
    path('booking/<int:booking_id>/review/edit/', views.edit_motorbike_review, name='edit_motorbike_review'),
    path('booking/<int:booking_id>/review/delete/', views.delete_motorbike_review, name='delete_motorbike_review'),
]