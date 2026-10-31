from django.urls import path
from . import views

urlpatterns = [
    path('', views.owner_dashboard, name='owner_dashboard'),
    path('guesthouse/<int:guesthouse_id>/bookings/', views.owner_guesthouse_bookings, name='owner_guesthouse_bookings'),
    path('booking/<int:booking_id>/check-in/', views.check_in_guest, name='check_in_guest'),
    path('tour/<int:tour_id>/bookings/', views.owner_tour_bookings, name='owner_tour_bookings'),
    path('tour-booking/<int:booking_id>/attended/', views.mark_attended, name='mark_attended'),
]