from datetime import date, timedelta, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q, Min, Max
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .forms import MotorbikeBookingForm, MotorbikeReviewForm, MotorbikeManagementForm
from .models import Motorbike, MotorbikeBooking, MotorbikeReview
from advisor.email_utils import (
    send_booking_confirmation_email, 
    send_booking_request_email, 
    send_booking_declined_email
)


# ==========================================
# 1. MOTORBIKE LISTING & DETAIL VIEWS
# ==========================================

def motorbike_list(request):
    """Home page: Lists all active motorbikes with advanced search and filtering."""
    motorbikes = Motorbike.objects.filter(is_active=True)
    
    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    # Apply text search filter
    if search_query:
        motorbikes = motorbikes.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Apply price range filter
    if min_price:
        try:
            motorbikes = motorbikes.filter(price_per_day__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            motorbikes = motorbikes.filter(price_per_day__lte=float(max_price))
        except ValueError:
            pass
    
    # Apply date availability filter
    if start_date and end_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # ✅ FIX: Use __lte and __gte to make end_date INCLUSIVE
            unavailable_ids = MotorbikeBooking.objects.filter(
                status__in=['pending', 'confirmed'],
                start_date__lte=end_date_obj,
                end_date__gte=start_date_obj
            ).values_list('motorbike_id', flat=True).distinct()
            
            # Exclude unavailable motorbikes
            motorbikes = motorbikes.exclude(id__in=unavailable_ids)
        except ValueError:
            pass
    
    # Get price range for the slider
    price_stats = Motorbike.objects.filter(is_active=True).aggregate(
        min_price=Min('price_per_day'),
        max_price=Max('price_per_day')
    )
    
    context = {
        'motorbikes': motorbikes,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
        'min_price': min_price or price_stats['min_price'],
        'max_price': max_price or price_stats['max_price'],
        'price_range': {
            'min': int(price_stats['min_price'] or 0),
            'max': int(price_stats['max_price'] or 100)
        }
    }
    
    return render(request, 'motorbike/motorbike_list.html', context)


def motorbike_detail(request, motorbike_id):
    """Detail page: Shows motorbike info and availability for next 30 days."""
    motorbike = get_object_or_404(Motorbike, id=motorbike_id, is_active=True)
    
    today = date.today()
    availability_schedule = []
    
    upcoming_bookings = MotorbikeBooking.objects.filter(
        motorbike=motorbike,
        status__in=['pending', 'confirmed'],
        end_date__gte=today
    )
    
    for i in range(30):
        current_day = today + timedelta(days=i)
        is_available = True
        
        for booking in upcoming_bookings:
            # ✅ FIX: Use <= for end_date to make it inclusive
            if booking.start_date <= current_day <= booking.end_date:
                is_available = False
                break
                
        availability_schedule.append({
            'date': current_day,
            'is_available': is_available,
            'day_name': current_day.strftime('%a'), 
            'day_num': current_day.day               
        })
        
    context = {
        'motorbike': motorbike,
        'availability': availability_schedule
    }
    
    return render(request, 'motorbike/motorbike_detail.html', context)


# ==========================================
# 2. MOTORBIKE BOOKING VIEWS (REQUEST & VERIFY)
# ==========================================

@login_required
def create_motorbike_booking(request, motorbike_id):
    """Handles the motorbike booking form submission - saves as PENDING for owner verification."""
    motorbike = get_object_or_404(Motorbike, id=motorbike_id, is_active=True)
    
    if request.method == 'POST':
        form = MotorbikeBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.motorbike = motorbike
            booking.guest = request.user
            booking.status = 'pending'
            
            try:
                booking.full_clean()
                booking.save()
                
                booking_reference = f"MB-{booking.id:04d}"
                send_booking_request_email(booking, booking_reference, 'motorbike')
                
                messages.success(request, 'Motorbike rental request received! The owner is verifying availability. You will receive a final confirmation email shortly.')
                
                return redirect('motorbike_booking_request_received', booking_id=booking.id)
            except ValidationError as e:
                form.add_error(None, e.messages[0])
    else:
        form = MotorbikeBookingForm()
    
    return render(request, 'motorbike/book_motorbike.html', {'form': form, 'motorbike': motorbike})


@login_required
def motorbike_booking_request_received(request, booking_id):
    """Displays a reassuring message that the motorbike request is being verified."""
    booking = get_object_or_404(MotorbikeBooking, id=booking_id, guest=request.user)
    return render(request, 'motorbike/motorbike_booking_request_received.html', {'booking': booking})


@login_required
def motorbike_booking_confirmation(request, booking_id):
    """Displays the motorbike booking voucher."""
    booking = get_object_or_404(MotorbikeBooking, id=booking_id, guest=request.user)
    booking_reference = f"MB-{booking.id:04d}"
    
    return render(request, 'motorbike/motorbike_booking_confirmation.html', {
        'booking': booking,
        'booking_reference': booking_reference
    })


@login_required
def cancel_motorbike_booking(request, booking_id):
    """Allows a user to cancel a pending or confirmed motorbike booking."""
    booking = get_object_or_404(MotorbikeBooking, id=booking_id, guest=request.user)
    
    if request.method == 'POST':
        if booking.status in ['pending', 'confirmed']:
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, 'Motorbike booking cancelled. Your dates have been released.')
        else:
            messages.info(request, 'This booking cannot be cancelled.')
        
        return redirect('motorbike_booking_confirmation', booking_id=booking.id)
    
    return render(request, 'motorbike/cancel_motorbike_booking.html', {'booking': booking})


# ==========================================
# 3. DASHBOARD & REVIEW VIEWS
# ==========================================

@login_required
def motorbike_bookings_dashboard(request):
    """Displays all motorbike bookings for the logged-in user, organized by upcoming, cancelled, and past."""
    today = timezone.now().date()
    
    all_bookings = MotorbikeBooking.objects.filter(guest=request.user).select_related('motorbike')
    
    upcoming_bookings = all_bookings.filter(
        end_date__gte=today,
        status__in=['pending', 'confirmed']
    ).order_by('start_date')
    
    cancelled_bookings = all_bookings.filter(
        status__in=['cancelled', 'refunded']
    ).order_by('-created_at')
    
    past_bookings = all_bookings.filter(
        end_date__lt=today,
        status__in=['pending', 'confirmed', 'completed']
    ).order_by('-start_date')
    
    context = {
        'upcoming_bookings': upcoming_bookings,
        'cancelled_bookings': cancelled_bookings,
        'past_bookings': past_bookings,
        'total_bookings': all_bookings.count(),
    }
    
    return render(request, 'motorbike/motorbike_bookings_dashboard.html', context)


@login_required
def submit_motorbike_review(request, booking_id):
    """Handles the submission of a motorbike review."""
    booking = get_object_or_404(MotorbikeBooking, id=booking_id, guest=request.user)
    
    if booking.status != 'confirmed':
        messages.error(request, 'You can only review confirmed bookings.')
        return redirect('motorbike_bookings_dashboard')
        
    if booking.end_date >= timezone.now().date():
        messages.error(request, 'You can only leave a review after your rental period has ended.')
        return redirect('motorbike_bookings_dashboard')
        
    if hasattr(booking, 'motorbike_review'):
        messages.info(request, 'You have already reviewed this motorbike.')
        return redirect('motorbike_bookings_dashboard')

    if request.method == 'POST':
        form = MotorbikeReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.motorbike = booking.motorbike
            review.guest = request.user
            review.save()
            messages.success(request, 'Thank you for your review!')
            return redirect('motorbike_detail', motorbike_id=booking.motorbike.id)
    else:
        form = MotorbikeReviewForm()

    return render(request, 'motorbike/submit_review.html', {
        'form': form,
        'booking': booking
    })


@login_required
def edit_motorbike_review(request, booking_id):
    """Allows a user to edit their existing motorbike review."""
    booking = get_object_or_404(MotorbikeBooking, id=booking_id, guest=request.user)
    
    if not hasattr(booking, 'motorbike_review'):
        messages.error(request, 'No review found for this booking.')
        return redirect('motorbike_bookings_dashboard')
    
    review = booking.motorbike_review

    if request.method == 'POST':
        form = MotorbikeReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your review has been updated!')
            return redirect('motorbike_detail', motorbike_id=booking.motorbike.id)
    else:
        form = MotorbikeReviewForm(instance=review)

    return render(request, 'motorbike/edit_review.html', {
        'form': form,
        'booking': booking,
        'review': review
    })


@login_required
def delete_motorbike_review(request, booking_id):
    """Allows a user to delete their motorbike review."""
    booking = get_object_or_404(MotorbikeBooking, id=booking_id, guest=request.user)
    
    if not hasattr(booking, 'motorbike_review'):
        messages.error(request, 'No review found for this booking.')
        return redirect('motorbike_bookings_dashboard')
    
    review = booking.motorbike_review

    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Your review has been deleted.')
        return redirect('motorbike_bookings_dashboard')
    
    return render(request, 'motorbike/confirm_delete_review.html', {
        'booking': booking,
        'review': review
    })


# ==========================================
# 4. OWNER DASHBOARD ACTIONS (MOTORBIKES)
# ==========================================

@login_required
def approve_motorbike_booking(request, booking_id):
    """Owner approves a pending motorbike booking."""
    booking = get_object_or_404(MotorbikeBooking, id=booking_id, motorbike__owner=request.user)
    
    if booking.status == 'pending':
        booking.status = 'confirmed'
        booking.save()
        
        booking_reference = f"MB-{booking.id:04d}"
        send_booking_confirmation_email(booking, booking_reference, 'motorbike')
        
        messages.success(request, f'Motorbike booking for {booking.guest.username} has been confirmed and they have been notified!')
    else:
        messages.info(request, 'This booking cannot be approved.')
        
    return redirect('owner_dashboard')


@login_required
def decline_motorbike_booking(request, booking_id):
    """Owner declines a pending motorbike booking with a reason."""
    booking = get_object_or_404(MotorbikeBooking, id=booking_id, motorbike__owner=request.user)
    
    if request.method == 'POST':
        if booking.status == 'pending':
            reason = request.POST.get('reason', '').strip()
            if not reason:
                reason = "The requested dates are no longer available."
            
            booking.status = 'cancelled'
            booking.save()
            
            booking_reference = f"MB-{booking.id:04d}"
            send_booking_declined_email(booking, booking_reference, 'motorbike', reason)
            
            messages.success(request, f'Motorbike booking for {booking.guest.username} has been declined. The guest has been notified.')
        else:
            messages.info(request, 'This booking cannot be declined.')
        
        return redirect('owner_dashboard')
    
    return redirect('owner_dashboard')


@login_required
def owner_motorbike_bookings(request, motorbike_id):
    """View all bookings for a specific motorbike."""
    if not request.user.groups.filter(name='Owner').exists() and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('motorbike_list')
    
    motorbike = get_object_or_404(Motorbike, id=motorbike_id, owner=request.user)
    today = timezone.now().date()
    
    bookings = MotorbikeBooking.objects.filter(
        motorbike=motorbike
    ).select_related('guest').order_by('-start_date')
    
    upcoming_bookings = bookings.filter(
        start_date__gte=today,
        status__in=['pending', 'confirmed']
    ).order_by('start_date')
    
    pending_bookings = bookings.filter(
        status='pending'
    ).order_by('start_date')
    
    past_bookings = bookings.filter(
        end_date__lt=today
    ).order_by('-start_date')
    
    context = {
        'motorbike': motorbike,
        'upcoming_bookings': upcoming_bookings,
        'pending_bookings': pending_bookings,
        'past_bookings': past_bookings,
    }
    
    return render(request, 'dashboard/owner_motorbike_bookings.html', context)


@login_required
def owner_motorbike_add(request):
    """Allows an owner to add a new motorbike."""
    if request.method == 'POST':
        form = MotorbikeManagementForm(request.POST)
        if form.is_valid():
            motorbike = form.save(commit=False)
            motorbike.owner = request.user
            motorbike.save()
            messages.success(request, f'"{motorbike.name}" has been successfully added!')
            return redirect('owner_dashboard')
    else:
        form = MotorbikeManagementForm()
        
    return render(request, 'dashboard/owner_motorbike_form.html', {
        'form': form,
        'title': 'Add New Motorbike'
    })


@login_required
def owner_motorbike_edit(request, motorbike_id):
    """Allows an owner to edit their existing motorbike."""
    motorbike = get_object_or_404(Motorbike, id=motorbike_id, owner=request.user)
    
    if request.method == 'POST':
        form = MotorbikeManagementForm(request.POST, instance=motorbike)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{motorbike.name}" has been updated successfully!')
            return redirect('owner_dashboard')
    else:
        form = MotorbikeManagementForm(instance=motorbike)
        
    return render(request, 'dashboard/owner_motorbike_form.html', {
        'form': form,
        'title': f'Edit: {motorbike.name}'
    })