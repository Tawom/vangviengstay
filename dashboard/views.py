from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone

from guesthouse.models import Booking, Guesthouse
from tours.models import TourBooking, Tour
from motorbike.models import Motorbike, MotorbikeBooking
from guides.models import GuideBooking, Guide
from buggy.models import BuggyCar, BuggyCarBooking


@login_required
def owner_dashboard(request):
    """Main dashboard overview for owners with stats and pending bookings."""
    if not request.user.groups.filter(name='Owner').exists() and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access the owner dashboard.')
        return redirect('guesthouse_list')
    
    today = timezone.now().date()
    
    my_guesthouses = Guesthouse.objects.filter(owner=request.user)
    my_tours = Tour.objects.filter(owner=request.user)
    my_motorbikes = Motorbike.objects.filter(owner=request.user)
    my_guides = Guide.objects.filter(owner=request.user)
    my_buggies = BuggyCar.objects.filter(owner=request.user)
    
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
    
    pending_bookings = Booking.objects.filter(guesthouse__owner=request.user, status='pending').select_related('guesthouse', 'guest').order_by('-created_at')
    pending_tour_bookings = TourBooking.objects.filter(tour__owner=request.user, status='pending').select_related('tour', 'guest').order_by('-created_at')
    pending_motorbike_bookings = MotorbikeBooking.objects.filter(motorbike__owner=request.user, status='pending').select_related('motorbike', 'guest').order_by('-created_at')
    pending_guide_bookings = GuideBooking.objects.filter(guide__owner=request.user, status='pending').select_related('guide', 'guest').order_by('-created_at')
    pending_buggy_bookings = BuggyCarBooking.objects.filter(buggy_car__owner=request.user, status='pending').select_related('buggy_car', 'guest').order_by('-created_at')
    
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
        'total_revenue': total_guesthouse_revenue + total_tour_revenue + total_motorbike_revenue + total_guide_revenue + total_buggy_revenue,
        'upcoming_guesthouse_checkins': upcoming_guesthouse_checkins,
        'upcoming_tour_departures': upcoming_tour_departures,
        'upcoming_guide_bookings_today': upcoming_guide_bookings_today,
        'pending_bookings': pending_bookings,
        'pending_tour_bookings': pending_tour_bookings,
        'pending_motorbike_bookings': pending_motorbike_bookings,
        'pending_guide_bookings': pending_guide_bookings,
        'pending_buggy_bookings': pending_buggy_bookings,
        'today': today,
    }
    
    return render(request, 'dashboard/owner_dashboard.html', context)


@login_required
def owner_guesthouse_bookings(request, guesthouse_id):
    if not request.user.groups.filter(name='Owner').exists() and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('guesthouse_list')
    
    guesthouse = get_object_or_404(Guesthouse, id=guesthouse_id, owner=request.user)
    today = timezone.now().date()
    
    bookings = Booking.objects.filter(guesthouse=guesthouse, status='confirmed').select_related('guest').order_by('check_in')
    
    context = {
        'guesthouse': guesthouse,
        'today_bookings': bookings.filter(check_in=today),
        'upcoming_bookings': bookings.filter(check_in__gt=today),
        'past_bookings': bookings.filter(check_out__lt=today),
    }
    
    return render(request, 'dashboard/owner_guesthouse_bookings.html', context)


@login_required
def check_in_guest(request, booking_id):
    if not request.user.groups.filter(name='Owner').exists() and not request.user.is_superuser:
        messages.error(request, 'Permission denied.')
        return redirect('guesthouse_list')
    
    booking = get_object_or_404(Booking, id=booking_id, guesthouse__owner=request.user)
    
    if request.method == 'POST':
        booking.checked_in = True
        booking.save()
        messages.success(request, f'{booking.guest.username|title} has been checked in successfully!')
    
    return redirect('owner_guesthouse_bookings', guesthouse_id=booking.guesthouse.id)


@login_required
def owner_tour_bookings(request, tour_id):
    if not request.user.groups.filter(name='Owner').exists() and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('guesthouse_list')
    
    tour = get_object_or_404(Tour, id=tour_id, owner=request.user)
    today = timezone.now().date()
    
    bookings = TourBooking.objects.filter(tour=tour, status='confirmed').select_related('guest').order_by('booking_date')
    
    context = {
        'tour': tour,
        'today_bookings': bookings.filter(booking_date=today),
        'upcoming_bookings': bookings.filter(booking_date__gt=today),
        'past_bookings': bookings.filter(booking_date__lt=today),
    }
    
    return render(request, 'dashboard/owner_tour_bookings.html', context)


@login_required
def mark_attended(request, booking_id):
    if not request.user.groups.filter(name='Owner').exists() and not request.user.is_superuser:
        messages.error(request, 'Permission denied.')
        return redirect('guesthouse_list')
    
    booking = get_object_or_404(TourBooking, id=booking_id, tour__owner=request.user)
    
    if request.method == 'POST':
        booking.attended = True
        booking.save()
        messages.success(request, f'{booking.guest.username|title} marked as attended!')
    
    return redirect('owner_tour_bookings', tour_id=booking.tour.id)


@login_required
def universal_dashboard(request):
    """Universal dashboard for guests showing all their bookings across all services."""
    print("🚀🚀🚀 UNIVERSAL DASHBOARD VIEW IS RUNNING! 🚀🚀🚀")
    
    today = timezone.now().date()
    print(f"DEBUG: Server 'today' is {today}")
    print(f"DEBUG: Current user is {request.user.username} (ID: {request.user.id})")
    
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
    
    # 🔍 DETAILED BUGGY DEBUGGING
    all_buggy_for_user = BuggyCarBooking.objects.filter(guest=request.user)
    print(f"DEBUG: ALL buggy bookings for {request.user.username}: {all_buggy_for_user.count()}")
    for b in all_buggy_for_user:
        print(f"  - ID: {b.id} | Date: {b.booking_date} | Status: {b.status} | >= today? {b.booking_date >= today}")
    
    buggy_upcoming = BuggyCarBooking.objects.filter(
        guest=request.user,
        booking_date__gte=today,
        status__in=['pending', 'confirmed']
    ).select_related('buggy_car').order_by('booking_date', 'start_time')
    
    print(f"DEBUG: Buggy upcoming count = {buggy_upcoming.count()}")
    
    total_bookings = (
        guesthouse_upcoming.count() + 
        tour_upcoming.count() + 
        guide_upcoming.count() + 
        motorbike_upcoming.count() +
        buggy_upcoming.count()
    )
    
    print(f"DEBUG: Calculated total_bookings = {total_bookings}")
    
    context = {
        'guesthouse_upcoming': guesthouse_upcoming,
        'tour_upcoming': tour_upcoming,
        'guide_upcoming': guide_upcoming,
        'motorbike_upcoming': motorbike_upcoming,
        'buggy_upcoming': buggy_upcoming,
        'total_bookings': total_bookings,
    }
    
    return render(request, 'dashboard/universal_dashboard.html', context)