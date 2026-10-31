from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # 1. Public Guesthouse Views
    # ==========================================
    path('', views.guesthouse_list, name='guesthouse_list'),
    path('<int:guesthouse_id>/', views.guesthouse_detail, name='guesthouse_detail'),
    path('<int:guesthouse_id>/book/', views.create_booking, name='create_booking'),
    
    # ==========================================
    # 2. Booking Management (Guest)
    # ==========================================
    path('booking/<int:booking_id>/request-received/', views.booking_request_received, name='booking_request_received'),
    path('booking/<int:booking_id>/confirmation/', views.booking_confirmation, name='booking_confirmation'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    
    # ==========================================
    # 3. User Dashboards
    # ==========================================
    path('my-dashboard/', views.universal_dashboard, name='universal_dashboard'),
    path('my-bookings/', views.guesthouse_bookings_dashboard, name='guesthouse_bookings_dashboard'),
    
    # ==========================================
    # 4. Owner Dashboard & Management
    # ==========================================
    path('owner/dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/guesthouses/add/', views.owner_guesthouse_add, name='owner_guesthouse_add'),
    path('owner/guesthouses/<int:pk>/edit/', views.owner_guesthouse_edit, name='owner_guesthouse_edit'),
    
    # Owner booking verification actions
    path('owner/bookings/<int:booking_id>/approve/', views.approve_booking, name='approve_booking'),
    path('owner/bookings/<int:booking_id>/decline/', views.decline_booking, name='decline_booking'),
    
    # ==========================================
    # 5. Authentication (Cleaned)
    # ==========================================
    path('signup/', views.signup_choice, name='signup_choice'),       # ✅ Main signup choice page
    path('signup/email/', views.signup_email, name='signup_email'),    # ✅ Email registration
    path('signup/phone/', views.signup_phone, name='signup_phone'),    # ✅ Phone registration
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # ==========================================
    # 6. Support
    # ==========================================
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('contact-us/', views.contact_us, name='contact_us'),
    path('contact-us/submit/', views.contact_us_submit, name='contact_us_submit'),
    
    # ==========================================
    # 7. Reviews
    # ==========================================
    path('booking/<int:booking_id>/review/', views.submit_guesthouse_review, name='submit_guesthouse_review'),
    path('booking/<int:booking_id>/review/edit/', views.edit_guesthouse_review, name='edit_guesthouse_review'),
    path('booking/<int:booking_id>/review/delete/', views.delete_guesthouse_review, name='delete_guesthouse_review'),
]