from django.urls import path
from . import views

urlpatterns = [
    path('', views.inquiry_view, name='inquiry'),
    path('success/', views.inquiry_success, name='inquiry_success'),
]