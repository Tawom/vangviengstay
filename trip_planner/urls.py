from django.urls import path
from . import views

urlpatterns = [
    path('', views.trip_plan, name='trip_plan'),
    path('success/', views.trip_plan_success, name='trip_plan_success'),
]