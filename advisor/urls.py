"""
URL configuration for advisor project.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

from .sitemaps import (
    StaticSitemap,
    TourSitemap,
    GuesthouseSitemap,
    MotorbikeSitemap,
    BuggySitemap,
    GuideSitemap,
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

# ==========================================
# 1. NON-LANGUAGED URLS (No /en/ or /lo/ prefix)
# These remain outside i18n_patterns
# ==========================================
urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Analytics (no language prefix)
    path('analytics/', include('analytics.urls')),

    # SEO & Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),

    # ✅ CRITICAL: Language switcher endpoint MUST be outside i18n_patterns
    path('i18n/', include('django.conf.urls.i18n')),

    # ✅ API endpoints (no language prefix)
    path('api/', include('advisor.api_urls')),
]

# ==========================================
# 2. LANGUAGED URLS (Will get /en/ or /lo/ prefix)
# ==========================================
urlpatterns += i18n_patterns(
    # --- Authentication (Password Reset) ---
    path('accounts/password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             success_url='/accounts/password-reset/done/',
         ),
         name='password_reset'),

    path('accounts/password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html',
         ),
         name='password_reset_done'),

    path('accounts/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/accounts/reset/done/',
         ),
         name='password_reset_confirm'),

    path('accounts/reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html',
         ),
         name='password_reset_complete'),

    # --- Contact / Inquiry ---
    path('contact/', include('inquiry.urls')),

    # --- App URLs ---
    path('', include('tours.urls')),
    #path('guesthouses/', include('guesthouse.urls')),
    path('motorbike/', include('motorbike.urls')),
    path('buggy/', include('buggy.urls')),
    path('guides/', include('guides.urls')),
    path('owner-dashboard/', include('dashboard.urls')),
    path('ai-assistant/', include('ai_assistant.urls')),

    # ✅ Keyword arguments must come LAST
    prefix_default_language=True,
)

# ==========================================
# 3. SERVE MEDIA & STATIC FILES (Development Only)
# ==========================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)