from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q, Min, Max
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .forms import BuggyCarBookingForm, BuggyCarReviewForm, BuggyCarManagementForm
from .models import BuggyCar, BuggyCarBooking, BuggyCarReview
from advisor.email_utils import (
    send_booking_confirmation_email,
    send_booking_request_email,
    send_booking_declined_email
)


# ==========================================
# 1. BUGGY CAR LISTING & DETAIL VIEWS
# ==========================================

def buggy_list(request):
    """List all active buggy cars with search and filtering."""
    buggies = BuggyCar.objects.filter(is_active=True)
    
    search_query = request.GET.get('search', '').strip()
    size_filter = request.GET.get('size', '')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if search_query:
        buggies = buggies.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if size_filter:
        buggies = buggies.filter(size=size_filter)
    
    if min_price:
        try:
            buggies = buggies.filter(price_2_hours__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            buggies = buggies.filter(price_2_hours__lte=float(max_price))
        except ValueError:
            pass
    
    price_stats = BuggyCar.objects.filter(is_active=True).aggregate(
        min_price=Min('price_2_hours'),
        max_price=Max('price_2_hours')
    )
    
    context = {
        'buggies': buggies,
        'search_query': search_query,
        'size_filter': size_filter,
        'min_price': min_price or price_stats['min_price'],
        'max_price': max_price or price_stats['max_price'],
        'price_range': {
            'min': int(price_stats['min_price'] or 0),
            'max': int(price_stats['max_price'] or 100)
        }
    }
    
    return render(request, 'buggy/buggy_list.html', context)


def buggy_detail(request, buggy_id):
    """Detail page for a specific buggy car."""
    buggy = get_object_or_404(BuggyCar, id=buggy_id, is_active=True)
    
    context = {
        'buggy': buggy,
    }
    
    return render(request, 'buggy/buggy_detail.html', context)


# ==========================================
# 2. BUGGY CAR BOOKING VIEWS (REQUEST & VERIFY)
# ==========================================

@login_required
def create_buggy_booking(request, buggy_id):
    """Handles the buggy booking form - saves as PENDING for owner verification."""
    buggy = get_object_or_404(BuggyCar, id=buggy_id, is_active=True)
    
    if request.method == 'POST':
        form = BuggyCarBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.buggy_car = buggy
            booking.guest = request.user
            booking.status = 'pending'
            
            try:
                booking.full_clean()
                booking.save()
                
                booking_reference = f"BG-{booking.id:04d}"
                send_booking_request_email(booking, booking_reference, 'buggy')
                
                messages.success(request, 'Buggy car booking request received! The owner is verifying availability.')
                return redirect('buggy_booking_request_received', booking_id=booking.id)
            except ValidationError as e:
                form.add_error(None, e.messages[0])
    else:
        form = BuggyCarBookingForm()
    
    return render(request, 'buggy/book_buggy.html', {'form': form, 'buggy': buggy})


@login_required
def buggy_booking_request_received(request, booking_id):
    """Displays a reassuring message that the buggy request is being verified."""
    booking = get_object_or_404(BuggyCarBooking, id=booking_id, guest=request.user)
    return render(request, 'buggy/buggy_booking_request_received.html', {'booking': booking})


@login_required
def buggy_booking_confirmation(request, booking_id):
    """Displays the buggy booking voucher."""
    booking = get_object_or_404(BuggyCarBooking, id=booking_id, guest=request.user)
    booking_reference = f"BG-{booking.id:04d}"
    
    return render(request, 'buggy/buggy_booking_confirmation.html', {
        'booking': booking,
        'booking_reference': booking_reference
    })


@login_required
def cancel_buggy_booking(request, booking_id):
    """Allows a user to cancel a pending or confirmed buggy booking."""
    booking = get_object_or_404(BuggyCarBooking, id=booking_id, guest=request.user)
    
    if request.method == 'POST':
        if booking.status in ['pending', 'confirmed']:
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, 'Buggy booking cancelled. Your slot has been released.')
        else:
            messages.info(request, 'This booking cannot be cancelled.')
        
        return redirect('buggy_booking_confirmation', booking_id=booking.id)
    
    return render(request, 'buggy/cancel_buggy_booking.html', {'booking': booking})


# ==========================================
# 3. DASHBOARD & REVIEW VIEWS
# ==========================================

@login_required
def buggy_bookings_dashboard(request):
    """Displays all buggy bookings for the logged-in user."""
    today = timezone.now().date()
    
    all_bookings = BuggyCarBooking.objects.filter(guest=request.user).select_related('buggy_car')
    
    upcoming_bookings = all_bookings.filter(
        booking_date__gte=today,
        status__in=['pending', 'confirmed']
    ).order_by('booking_date', 'start_time')
    
    cancelled_bookings = all_bookings.filter(
        status__in=['cancelled', 'refunded']
    ).order_by('-created_at')
    
    past_bookings = all_bookings.filter(
        booking_date__lt=today,
        status__in=['pending', 'confirmed', 'completed']
    ).order_by('-booking_date')
    
    context = {
        'upcoming_bookings': upcoming_bookings,
        'cancelled_bookings': cancelled_bookings,
        'past_bookings': past_bookings,
        'total_bookings': all_bookings.count(),
    }
    
    return render(request, 'buggy/buggy_bookings_dashboard.html', context)


@login_required
def submit_buggy_review(request, booking_id):
    """Handles the submission of a buggy review."""
    booking = get_object_or_404(BuggyCarBooking, id=booking_id, guest=request.user)
    
    if booking.status != 'confirmed':
        messages.error(request, 'You can only review confirmed bookings.')
        return redirect('buggy_bookings_dashboard')
    
    if hasattr(booking, 'buggy_review'):
        messages.info(request, 'You have already reviewed this buggy car.')
        return redirect('buggy_bookings_dashboard')
    
    if request.method == 'POST':
        form = BuggyCarReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.buggy_car = booking.buggy_car
            review.guest = request.user
            review.save()
            messages.success(request, 'Thank you for your review!')
            return redirect('buggy_detail', buggy_id=booking.buggy_car.id)
    else:
        form = BuggyCarReviewForm()
    
    return render(request, 'buggy/submit_review.html', {
        'form': form,
        'booking': booking
    })


# ==========================================
# 4. OWNER DASHBOARD ACTIONS (BUGGY CARS)
# ==========================================

@login_required
def approve_buggy_booking(request, booking_id):
    """Owner approves a pending buggy booking."""
    booking = get_object_or_404(BuggyCarBooking, id=booking_id, buggy_car__owner=request.user)
    
    if booking.status == 'pending':
        booking.status = 'confirmed'
        booking.save()
        
        booking_reference = f"BG-{booking.id:04d}"
        send_booking_confirmation_email(booking, booking_reference, 'buggy')
        
        messages.success(request, f'Buggy booking for {booking.guest.username} has been confirmed!')
    else:
        messages.info(request, 'This booking cannot be approved.')
    
    return redirect('owner_dashboard')


@login_required
def decline_buggy_booking(request, booking_id):
    """Owner declines a pending buggy booking with a reason."""
    booking = get_object_or_404(BuggyCarBooking, id=booking_id, buggy_car__owner=request.user)
    
    if request.method == 'POST':
        if booking.status == 'pending':
            reason = request.POST.get('reason', '').strip()
            if not reason:
                reason = "The buggy is unavailable for the requested time."
            
            booking.status = 'cancelled'
            booking.save()
            
            booking_reference = f"BG-{booking.id:04d}"
            send_booking_declined_email(booking, booking_reference, 'buggy', reason)
            
            messages.success(request, f'Buggy booking for {booking.guest.username} has been declined.')
        else:
            messages.info(request, 'This booking cannot be declined.')
        
        return redirect('owner_dashboard')
    
    return redirect('owner_dashboard')


@login_required
def owner_buggy_add(request):
    """Allows an owner to add a new buggy car."""
    if request.method == 'POST':
        form = BuggyCarManagementForm(request.POST)
        if form.is_valid():
            buggy = form.save(commit=False)
            buggy.owner = request.user
            buggy.save()
            messages.success(request, f'"{buggy.name}" has been successfully added!')
            return redirect('owner_dashboard')
    else:
        form = BuggyCarManagementForm()
    
    return render(request, 'dashboard/owner_buggy_form.html', {
        'form': form,
        'title': 'Add New Buggy Car'
    })


@login_required
def owner_buggy_edit(request, buggy_id):
    """Allows an owner to edit their existing buggy car."""
    buggy = get_object_or_404(BuggyCar, id=buggy_id, owner=request.user)
    
    if request.method == 'POST':
        form = BuggyCarManagementForm(request.POST, instance=buggy)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{buggy.name}" has been updated successfully!')
            return redirect('owner_dashboard')
    else:
        form = BuggyCarManagementForm(instance=buggy)
    
    return render(request, 'dashboard/owner_buggy_form.html', {
        'form': form,
        'title': f'Edit: {buggy.name}'
    })