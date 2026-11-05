"""
URL configuration for advisor project.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap

from .sitemaps import (
    StaticSitemap, 
    TourSitemap, 
    GuesthouseSitemap, 
    MotorbikeSitemap, 
    BuggySitemap, 
    GuideSitemap
)

# Combine all sitemaps into one dictionary
sitemaps = {
    'static': StaticSitemap,
    'tours': TourSitemap,
    'guesthouses': GuesthouseSitemap,
    'motorbikes': MotorbikeSitemap,
    'buggies': BuggySitemap,
    'guides': GuideSitemap,
}

urlpatterns = [
    # ==========================================
    # 1. ADMIN & ANALYTICS
    # ==========================================
    path('admin/', admin.site.urls),
    path('analytics/', include('analytics.urls')),
    
    # ==========================================
    # 2. SEO & SITEMAP
    # ==========================================
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    
    # ==========================================
    # 3. AUTHENTICATION (Password Reset)
    # ==========================================
    path('accounts/password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url='/accounts/password-reset/done/'
    ), name='password_reset'),
    
    path('accounts/password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/accounts/reset/done/'
    ), name='password_reset_confirm'),
    
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # ==========================================
    # 4. APP URLS
    # ==========================================
    path('', include('guesthouse.urls')),
    path('tours/', include('tours.urls')),
    path('motorbike/', include('motorbike.urls')),
    path('buggy/', include('buggy.urls')),
    path('guides/', include('guides.urls')),
    path('owner-dashboard/', include('dashboard.urls')),
    path('ai-assistant/', include('ai_assistant.urls')),
]