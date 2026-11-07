from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from guesthouse.models import Booking, Guesthouse
from tours.models import TourBooking, Tour
from motorbike.models import Motorbike, MotorbikeBooking
from guides.models import GuideBooking, Guide
from buggy.models import BuggyCar, BuggyCarBooking


# ==========================================
# 1. OWNER DASHBOARD
# ==========================================

@login_required
def owner_dashboard(request):
    """Main dashboard overview for owners with stats and pending bookings."""
    if not request.user.groups.filter(name='Owner').exists() and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access the owner dashboard.')
        return redirect('guesthouse_list')
    
    today = timezone.now().date()
    
    # Get all owner's properties
    my_guesthouses = Guesthouse.objects.filter(owner=request.user)
    my_tours = Tour.objects.filter(owner=request.user)
    my_motorbikes = Motorbike.objects.filter(owner=request.user)
    my_guides = Guide.objects.filter(owner=request.user)
    my_buggies = BuggyCar.objects.filter(owner=request.user)
    
    # Calculate revenue for each category
    guesthouse_bookings = Booking.objects.filter(guesthouse__owner=request.user, status='confirmed')
    total_guesthouse_revenue = guesthouse_bookings.aggregate(total=Sum('total_price'))['total'] or 0
    upcoming_guesthouse_checkins = guesthouse_bookings.filter(check_in=today, checked_in=False).count()
    
    tour_bookings = TourBooking.objects.filter(tour__owner=request.user, status='confirmed')
    total_tour_revenue = tour_bookings.aggregate(total=Sum('total_price'))['total'] or 0
    upcoming_tour_departures = tour_bookings.filter(booking_date=today, attended=False).count()
    
    motorbike_bookings = MotorbikeBooking.objects.filter(motorbike__owner=request.user, status='confirmed')
    total_motorbike_revenue = motorbike_bookings.aggregate(total=Sum('total_price'))['total'] or 0
    
    guide_bookings = GuideBooking.objects.filter(guide__owner=request.user, status='confirmed')
    total_guide_revenue = guide_bookings.aggregate(total=Sum('total_price'))['total'] or 0
    upcoming_guide_bookings_today = guide_bookings.filter(booking_date=today, attended=False).count()
    
    buggy_bookings = BuggyCarBooking.objects.filter(buggy_car__owner=request.user, status='confirmed')
    total_buggy_revenue = buggy_bookings.aggregate(total=Sum('total_price'))['total'] or 0
    
    # Get pending bookings for all categories
    pending_bookings = Booking.objects.filter(
        guesthouse__owner=request.user, status='pending'
    ).select_related('guesthouse', 'guest').order_by('-created_at')
    
    pending_tour_bookings = TourBooking.objects.filter(
        tour__owner=request.user, status='pending'
    ).select_related('tour', 'guest').order_by('-created_at')
    
    pending_motorbike_bookings = MotorbikeBooking.objects.filter(
        motorbike__owner=request.user, status='pending'
    ).select_related('motorbike', 'guest').order_by('-created_at')
    
    pending_guide_bookings = GuideBooking.objects.filter(
        guide__owner=request.user, status='pending'
    ).select_related('guide', 'guest').order_by('-created_at')
    
    pending_buggy_bookings = BuggyCarBooking.objects.filter(
        buggy_car__owner=request.user, status='pending'
    ).select_related('buggy_car', 'guest').order_by('-created_at')
    
    context = {
        'my_guesthouses': my_guesthouses,
        'my_tours': my_tours,
        'my_motorbikes': my_motorbikes,
        'my_guides': my_guides,
        'my_buggies': my_buggies,
        'total_properties': my_guesthouses.count(),
        'active_properties': my_guesthouses.filter(is_active=True).count(),
        'total_guesthouse_revenue': total_guesthouse_revenue,
        'total_tour_revenue': total_tour_revenue,
        'total_motorbike_revenue': total_motorbike_revenue,
        'total_guide_revenue': total_guide_revenue,
        'total_buggy_revenue': total_buggy_revenue,
        'total_revenue': (
            total_guesthouse_revenue + total_tour_revenue + 
            total_motorbike_revenue + total_guide_revenue + total_buggy_revenue
        ),
        'upcoming_guesthouse_checkins': upcoming_guesthouse_checkins,
        'upcoming_tour_departures': upcoming_tour_departures,
        'upcoming_guide_bookings_today': upcoming_guide_bookings_today,
        'pending_bookings': pending_bookings,
        'pending_tour_bookings': pending_tour_bookings,
        'pending_motorbike_bookings': pending_motorbike_bookings,
        'pending_guide_bookings': pending_guide_bookings,
        'pending_buggy_bookings': pending_buggy_bookings,
        'total_pending_requests': (
            pending_bookings.count() + 
            pending_tour_bookings.count() + 
            pending_motorbike_bookings.count() + 
            pending_guide_bookings.count() + 
            pending_buggy_bookings.count()
        ),
        'today': today,
    }
    
    return render(request, 'dashboard/owner_dashboard.html', context)


# ==========================================
# 2. GUESTHOUSE BOOKINGS MANAGEMENT
# ==========================================

@login_required
def owner_guesthouse_bookings(request, guesthouse_id):
    """View all bookings for a specific guesthouse."""
    if not request.user.groups.filter(name='Owner').exists() and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('guesthouse_list')
    
    guesthouse = get_object_or_404(Guesthouse, id=guesthouse_id, owner=request.user)
    today = timezone.now().date()
    
    bookings = Booking.objects.filter(
        guesthouse=guesthouse, status='confirmed'
    ).select_related('guest').order_by('check_in')
    
    context = {
        'guesthouse': guesthouse,
        'today_bookings': bookings.filter(check_in=today),
        'upcoming_bookings': bookings.filter(check_in__gt=today),
        'past_bookings': bookings.filter(check_out__lt=today),
    }
    
    return render(request, 'dashboard/owner_guesthouse_bookings.html', context)


@login_required
def check_in_guest(request, booking_id):
    """Mark a guest as checked in."""
    if not request.user.groups.filter(name='Owner').exists() and not request.user.is_superuser:
        messages.error(request, 'Permission denied.')
        return redirect('guesthouse_list')
    
    booking = get_object_or_404(Booking, id=booking_id, guesthouse__owner=request.user)
    
    if request.method == 'POST':
        booking.checked_in = True
        booking.save()
        messages.success(request, f'{booking.guest.username} has been checked in successfully!')
    
    return redirect('owner_guesthouse_bookings', guesthouse_id=booking.guesthouse.id)


# ==========================================
# 3. TOUR BOOKINGS MANAGEMENT
# ==========================================

@login_required
def owner_tour_bookings(request, tour_id):
    """View all bookings for a specific tour."""
    if not request.user.groups.filter(name='Owner').exists() and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('guesthouse_list')
    
    tour = get_object_or_404(Tour, id=tour_id, owner=request.user)
    today = timezone.now().date()
    
    bookings = TourBooking.objects.filter(
        tour=tour, status='confirmed'
    ).select_related('guest').order_by('booking_date')
    
    context = {
        'tour': tour,
        'today_bookings': bookings.filter(booking_date=today),
        'upcoming_bookings': bookings.filter(booking_date__gt=today),
        'past_bookings': bookings.filter(booking_date__lt=today),
    }
    
    return render(request, 'dashboard/owner_tour_bookings.html', context)


@login_required
def mark_attended(request, booking_id):
    """Mark a tour participant as attended."""
    if not request.user.groups.filter(name='Owner').exists() and not request.user.is_superuser:
        messages.error(request, 'Permission denied.')
        return redirect('guesthouse_list')
    
    booking = get_object_or_404(TourBooking, id=booking_id, tour__owner=request.user)
    
    if request.method == 'POST':
        booking.attended = True
        booking.save()
        messages.success(request, f'{booking.guest.username} marked as attended!')
    
    return redirect('owner_tour_bookings', tour_id=booking.tour.id)


# ==========================================
# 4. UNIVERSAL DASHBOARD (FOR GUESTS)
# ==========================================

@login_required
def universal_dashboard(request):
    """Universal dashboard for guests showing all their bookings across all services."""
    today = timezone.now().date()
    
    guesthouse_upcoming = Booking.objects.filter(
        guest=request.user,
        check_out__gte=today,
        status__in=['pending', 'confirmed']
    ).select_related('guesthouse').order_by('check_in')
    
    tour_upcoming = TourBooking.objects.filter(
        guest=request.user,
        booking_date__gte=today,
        status__in=['pending', 'confirmed']
    ).select_related('tour').order_by('booking_date')
    
    guide_upcoming = GuideBooking.objects.filter(
        guest=request.user,
        booking_date__gte=today,
        status__in=['pending', 'confirmed']
    ).select_related('guide').order_by('booking_date', 'start_time')
    
    motorbike_upcoming = MotorbikeBooking.objects.filter(
        guest=request.user,
        end_date__gte=today,
        status__in=['pending', 'confirmed']
    ).select_related('motorbike').order_by('start_date')
    
    buggy_upcoming = BuggyCarBooking.objects.filter(
        guest=request.user,
        booking_date__gte=today,
        status__in=['pending', 'confirmed']
    ).select_related('buggy_car').order_by('booking_date', 'start_time')
    
    total_bookings = (
        guesthouse_upcoming.count() + 
        tour_upcoming.count() + 
        guide_upcoming.count() + 
        motorbike_upcoming.count() +
        buggy_upcoming.count()
    )
    
    context = {
        'guesthouse_upcoming': guesthouse_upcoming,
        'tour_upcoming': tour_upcoming,
        'guide_upcoming': guide_upcoming,
        'motorbike_upcoming': motorbike_upcoming,
        'buggy_upcoming': buggy_upcoming,
        'total_bookings': total_bookings,
    }
    
    return render(request, 'dashboard/universal_dashboard.html', context)


# ==========================================
# 5. ADVANCED OWNER ANALYTICS
# ==========================================

@login_required
def owner_analytics(request):
    """Advanced analytics dashboard for property owners."""
    if not request.user.groups.filter(name='Owner').exists() and not request.user.is_superuser:
        messages.warning(request, "You do not have owner permissions.")
        return redirect('guesthouse_list')
    
    # Get date range from URL params (default: last 30 days)
    period = request.GET.get('period', '30')
    period_map = {
        '7': 7,
        '30': 30,
        '90': 90,
        '365': 365,
        'all': None
    }
    days = period_map.get(period, 30)
    
    if days:
        start_date = timezone.now().date() - timedelta(days=days)
    else:
        start_date = None
    
    # Get all owner's properties
    owner_guesthouses = Guesthouse.objects.filter(owner=request.user)
    owner_tours = Tour.objects.filter(owner=request.user)
    owner_guides = Guide.objects.filter(owner=request.user)
    owner_motorbikes = Motorbike.objects.filter(owner=request.user)
    owner_buggies = BuggyCar.objects.filter(owner=request.user)
    
    # Calculate revenue for each category
    def calculate_revenue(model, owner_field, start_date):
        qs = model.objects.filter(
            **{owner_field: request.user},
            status__in=['confirmed', 'completed']
        )
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        return qs.aggregate(total=Sum('total_price'))['total'] or Decimal('0')
    
    gh_revenue_total = calculate_revenue(Booking, 'guesthouse__owner', start_date)
    tour_revenue_total = calculate_revenue(TourBooking, 'tour__owner', start_date)
    guide_revenue_total = calculate_revenue(GuideBooking, 'guide__owner', start_date)
    motorbike_revenue_total = calculate_revenue(MotorbikeBooking, 'motorbike__owner', start_date)
    buggy_revenue_total = calculate_revenue(BuggyCarBooking, 'buggy_car__owner', start_date)
    
    total_revenue = (
        gh_revenue_total + tour_revenue_total + guide_revenue_total + 
        motorbike_revenue_total + buggy_revenue_total
    )
    
    # Count bookings by status
    def count_bookings(model, owner_field, status_filter, start_date):
        qs = model.objects.filter(**{f'{owner_field}': request.user, 'status__in': status_filter})
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        return qs.count()
    
    total_confirmed = (
        count_bookings(Booking, 'guesthouse__owner', ['confirmed', 'completed'], start_date) +
        count_bookings(TourBooking, 'tour__owner', ['confirmed', 'completed'], start_date) +
        count_bookings(GuideBooking, 'guide__owner', ['confirmed', 'completed'], start_date) +
        count_bookings(MotorbikeBooking, 'motorbike__owner', ['confirmed', 'completed'], start_date) +
        count_bookings(BuggyCarBooking, 'buggy_car__owner', ['confirmed', 'completed'], start_date)
    )
    
    total_pending = (
        count_bookings(Booking, 'guesthouse__owner', ['pending'], start_date) +
        count_bookings(TourBooking, 'tour__owner', ['pending'], start_date) +
        count_bookings(GuideBooking, 'guide__owner', ['pending'], start_date) +
        count_bookings(MotorbikeBooking, 'motorbike__owner', ['pending'], start_date) +
        count_bookings(BuggyCarBooking, 'buggy_car__owner', ['pending'], start_date)
    )
    
    total_cancelled = (
        count_bookings(Booking, 'guesthouse__owner', ['cancelled', 'refunded'], start_date) +
        count_bookings(TourBooking, 'tour__owner', ['cancelled'], start_date) +
        count_bookings(GuideBooking, 'guide__owner', ['cancelled'], start_date) +
        count_bookings(MotorbikeBooking, 'motorbike__owner', ['cancelled'], start_date) +
        count_bookings(BuggyCarBooking, 'buggy_car__owner', ['cancelled'], start_date)
    )
    
    total_bookings = total_confirmed + total_pending + total_cancelled
    conversion_rate = round((total_confirmed / total_bookings * 100), 1) if total_bookings > 0 else 0
    
    # Calculate reviews and ratings
    all_reviews = []
    for gh in owner_guesthouses:
        all_reviews.extend(gh.reviews.all())
    for tour in owner_tours:
        all_reviews.extend(tour.reviews.all())
    for guide in owner_guides:
        all_reviews.extend(guide.reviews.all())
    for mb in owner_motorbikes:
        all_reviews.extend(mb.reviews.all())
    for buggy in owner_buggies:
        all_reviews.extend(buggy.reviews.all())
    
    total_reviews = len(all_reviews)
    avg_rating = round(sum(r.rating for r in all_reviews) / total_reviews, 1) if total_reviews > 0 else 0
    
    # Chart data: Revenue by category
    revenue_by_category = {
        'labels': ['Guesthouses', 'Tours', 'Guides', 'Motorbikes', 'Buggy Cars'],
        'data': [
            float(gh_revenue_total),
            float(tour_revenue_total),
            float(guide_revenue_total),
            float(motorbike_revenue_total),
            float(buggy_revenue_total)
        ],
        'colors': ['#2563EB', '#16A34A', '#D97706', '#EA580C', '#9333EA']
    }
    
    # Top performing listings
    top_listings = []
    
    def get_listing_stats(model, booking_model, item, booking_field, category, color):
        revenue = booking_model.objects.filter(
            **{booking_field: item},
            status__in=['confirmed', 'completed']
        ).aggregate(total=Sum('total_price'))['total'] or Decimal('0')
        
        bookings = booking_model.objects.filter(
            **{booking_field: item},
            status__in=['confirmed', 'completed']
        ).count()
        
        return {
            'name': item.name,
            'category': category,
            'color': color,
            'revenue': revenue,
            'bookings': bookings,
            'rating': item.average_rating,
            'reviews': item.review_count
        }
    
    for gh in owner_guesthouses:
        top_listings.append(get_listing_stats(Guesthouse, Booking, gh, 'guesthouse', 'Guesthouse', 'blue'))
    
    for tour in owner_tours:
        top_listings.append(get_listing_stats(Tour, TourBooking, tour, 'tour', 'Tour', 'green'))
    
    for guide in owner_guides:
        top_listings.append(get_listing_stats(Guide, GuideBooking, guide, 'guide', 'Guide', 'amber'))
    
    for mb in owner_motorbikes:
        top_listings.append(get_listing_stats(Motorbike, MotorbikeBooking, mb, 'motorbike', 'Motorbike', 'orange'))
    
    for buggy in owner_buggies:
        top_listings.append(get_listing_stats(BuggyCar, BuggyCarBooking, buggy, 'buggy_car', 'Buggy Car', 'purple'))
    
    # Sort by revenue descending and take top 5
    top_listings.sort(key=lambda x: x['revenue'], reverse=True)
    top_listings = top_listings[:5]
    
    context = {
        'period': period,
        'total_revenue': total_revenue,
        'total_bookings': total_bookings,
        'total_confirmed': total_confirmed,
        'total_pending': total_pending,
        'total_cancelled': total_cancelled,
        'conversion_rate': conversion_rate,
        'total_reviews': total_reviews,
        'avg_rating': avg_rating,
        'revenue_by_category': revenue_by_category,
        'top_listings': top_listings,
        'total_properties': (
            owner_guesthouses.count() + owner_tours.count() + owner_guides.count() +
            owner_motorbikes.count() + owner_buggies.count()
        ),
    }
    
    return render(request, 'dashboard/owner_analytics.html', context)