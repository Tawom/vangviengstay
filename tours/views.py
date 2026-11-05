from datetime import date, timedelta, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q, Min, Max
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from advisor.utils import get_booking_confirmation_message
from .forms import TourBookingForm, TourReviewForm, TourManagementForm
from .models import Tour, TourBooking, TourReview
from advisor.email_utils import (
    send_booking_confirmation_email, 
    send_booking_request_email, 
    send_booking_declined_email
)


# ==========================================
# 1. TOUR LISTING & DETAIL VIEWS
# ==========================================

def tour_list(request):
    """Home page: Lists all active tours with advanced search and filtering."""
    tours = Tour.objects.filter(is_active=True)
    
    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    tour_date = request.GET.get('tour_date')
    duration_filter = request.GET.get('duration', '')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    max_guests = request.GET.get('max_guests')
    
    # Apply text search filter
    if search_query:
        tours = tours.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(operator_name__icontains=search_query)
        )
    
    # Apply duration filter
    if duration_filter:
        try:
            duration_value = float(duration_filter)
            if duration_value == 4:
                tours = tours.filter(duration_hours__lt=4)
            elif duration_value == 8:
                tours = tours.filter(duration_hours__gte=4, duration_hours__lte=8)
            elif duration_value == 12:
                tours = tours.filter(duration_hours__gt=8)
        except ValueError:
            pass
    
    # Apply price range filter
    if min_price:
        try:
            tours = tours.filter(price_per_person__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            tours = tours.filter(price_per_person__lte=float(max_price))
        except ValueError:
            pass
    
    # Apply max guests filter
    if max_guests:
        try:
            tours = tours.filter(max_capacity__gte=int(max_guests))
        except ValueError:
            pass
    
    # Apply date availability filter
    if tour_date:
        try:
            selected_date = datetime.strptime(tour_date, '%Y-%m-%d').date()
            
            bookings_on_date = TourBooking.objects.filter(
                booking_date=selected_date,
                status__in=['pending', 'confirmed']
            )
            
            available_tour_ids = []
            for tour in tours:
                total_booked = sum(
                    booking.number_of_people 
                    for booking in bookings_on_date 
                    if booking.tour_id == tour.id
                )
                available_spots = tour.max_capacity - total_booked
                if available_spots > 0:
                    available_tour_ids.append(tour.id)
            
            tours = tours.filter(id__in=available_tour_ids)
        except ValueError:
            pass
    
    # Get price range for the slider
    price_stats = Tour.objects.filter(is_active=True).aggregate(
        min_price=Min('price_per_person'),
        max_price=Max('price_per_person')
    )
    
    context = {
        'tours': tours,
        'search_query': search_query,
        'tour_date': tour_date,
        'duration_filter': duration_filter,
        'min_price': min_price or price_stats['min_price'],
        'max_price': max_price or price_stats['max_price'],
        'max_guests': max_guests,
        'price_range': {
            'min': int(price_stats['min_price'] or 0),
            'max': int(price_stats['max_price'] or 100)
        }
    }
    
    return render(request, 'tours/tour_list.html', context)


def tour_detail(request, tour_id):
    """Detail page: Shows tour info and availability for next 30 days."""
    tour = get_object_or_404(Tour, id=tour_id, is_active=True)
    
    today = date.today()
    availability_schedule = []
    
    upcoming_bookings = TourBooking.objects.filter(
        tour=tour,
        status__in=['pending', 'confirmed'],
        booking_date__gte=today
    )
    
    for i in range(30):
        current_day = today + timedelta(days=i)
        
        total_booked = sum(
            booking.number_of_people 
            for booking in upcoming_bookings 
            if booking.booking_date == current_day
        )
        
        available_spots = tour.max_capacity - total_booked
        
        availability_schedule.append({
            'date': current_day,
            'available_spots': available_spots,
            'is_available': available_spots > 0,
            'day_name': current_day.strftime('%a'),
            'day_num': current_day.day
        })
    
    context = {
        'tour': tour,
        'availability': availability_schedule
    }
    
    return render(request, 'tours/tour_detail.html', context)


# ==========================================
# 2. TOUR BOOKING VIEWS (REQUEST & VERIFY)
# ==========================================

@login_required
def create_tour_booking(request, tour_id):
    """Handles the tour booking form submission - saves as PENDING for owner verification."""
    tour = get_object_or_404(Tour, id=tour_id, is_active=True)
    
    if request.method == 'POST':
        form = TourBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.tour = tour
            booking.guest = request.user
            booking.status = 'pending'
            
            try:
                booking.full_clean()
                booking.save()
                
                booking_reference = f"TV-{booking.id:04d}"
                send_booking_request_email(booking, booking_reference, 'tour')
                
                # ✅ IMPROVED UX: Use centralized utility for smart success message
                messages.success(request, get_booking_confirmation_message(booking, "Tour booking"))
                
                return redirect('tour_booking_request_received', booking_id=booking.id)
            
            except ValidationError as e:
                form.add_error(None, e.messages[0])
    else:
        form = TourBookingForm()
    
    return render(request, 'tours/book_tour.html', {'form': form, 'tour': tour})


@login_required
def tour_booking_request_received(request, booking_id):
    """Displays a reassuring message that the tour request is being verified."""
    booking = get_object_or_404(TourBooking, id=booking_id, guest=request.user)
    return render(request, 'tours/tour_booking_request_received.html', {'booking': booking})


@login_required
def tour_booking_confirmation(request, booking_id):
    """Displays the tour booking voucher."""
    booking = get_object_or_404(TourBooking, id=booking_id, guest=request.user)
    booking_reference = f"TV-{booking.id:04d}"
    
    return render(request, 'tours/tour_booking_confirmation.html', {
        'booking': booking,
        'booking_reference': booking_reference
    })


@login_required
def cancel_tour_booking(request, booking_id):
    """Allows a user to cancel a pending or confirmed tour booking."""
    booking = get_object_or_404(TourBooking, id=booking_id, guest=request.user)
    
    if request.method == 'POST':
        if booking.status in ['pending', 'confirmed']:
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, 'Tour booking cancelled. Your spot has been released.')
        else:
            messages.info(request, 'This booking cannot be cancelled.')
        
        return redirect('tour_booking_confirmation', booking_id=booking.id)
    
    return render(request, 'tours/cancel_tour_booking.html', {'booking': booking})


# ==========================================
# 3. DASHBOARD & REVIEW VIEWS
# ==========================================

@login_required
def tour_bookings_dashboard(request):
    """Displays all tour bookings for the logged-in user, organized by upcoming, cancelled, and past."""
    today = timezone.now().date()
    
    all_bookings = TourBooking.objects.filter(guest=request.user).select_related('tour')
    
    upcoming_bookings = all_bookings.filter(
        booking_date__gte=today,
        status__in=['pending', 'confirmed']
    ).order_by('booking_date', 'tour__departure_time')
    
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
    
    return render(request, 'tours/tour_bookings_dashboard.html', context)


@login_required
def submit_tour_review(request, booking_id):
    """Handles the submission of a tour review."""
    booking = get_object_or_404(TourBooking, id=booking_id, guest=request.user)
    
    if booking.status != 'confirmed':
        messages.error(request, 'You can only review confirmed bookings.')
        return redirect('tour_bookings_dashboard')
        
    if booking.booking_date >= timezone.now().date():
        messages.error(request, 'You can only leave a review after the tour has taken place.')
        return redirect('tour_bookings_dashboard')
        
    if hasattr(booking, 'tour_review'):
        messages.info(request, 'You have already reviewed this tour.')
        return redirect('tour_bookings_dashboard')

    if request.method == 'POST':
        form = TourReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.tour = booking.tour
            review.guest = request.user
            review.save()
            messages.success(request, 'Thank you for your review!')
            return redirect('tour_detail', tour_id=booking.tour.id)
    else:
        form = TourReviewForm()

    return render(request, 'tours/submit_review.html', {
        'form': form,
        'booking': booking
    })


@login_required
def edit_tour_review(request, booking_id):
    """Allows a user to edit their existing tour review."""
    booking = get_object_or_404(TourBooking, id=booking_id, guest=request.user)
    
    if not hasattr(booking, 'tour_review'):
        messages.error(request, 'No review found for this booking.')
        return redirect('tour_bookings_dashboard')
    
    review = booking.tour_review

    if request.method == 'POST':
        form = TourReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your review has been updated!')
            return redirect('tour_detail', tour_id=booking.tour.id)
    else:
        form = TourReviewForm(instance=review)

    return render(request, 'tours/edit_review.html', {
        'form': form,
        'booking': booking,
        'review': review
    })


@login_required
def delete_tour_review(request, booking_id):
    """Allows a user to delete their tour review."""
    booking = get_object_or_404(TourBooking, id=booking_id, guest=request.user)
    
    if not hasattr(booking, 'tour_review'):
        messages.error(request, 'No review found for this booking.')
        return redirect('tour_bookings_dashboard')
    
    review = booking.tour_review

    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Your review has been deleted.')
        return redirect('tour_bookings_dashboard')
    
    return render(request, 'tours/confirm_delete_review.html', {
        'booking': booking,
        'review': review
    })


# ==========================================
# 4. OWNER DASHBOARD ACTIONS (TOURS)
# ==========================================

@login_required
def approve_tour_booking(request, booking_id):
    """Owner approves a pending tour booking."""
    booking = get_object_or_404(TourBooking, id=booking_id, tour__owner=request.user)
    
    if booking.status == 'pending':
        booking.status = 'confirmed'
        booking.save()
        
        booking_reference = f"TV-{booking.id:04d}"
        send_booking_confirmation_email(booking, booking_reference, 'tour')
        
        messages.success(request, f'Tour booking for {booking.guest.username} has been confirmed and they have been notified!')
    else:
        messages.info(request, 'This booking cannot be approved.')
        
    return redirect('owner_dashboard')


@login_required
def decline_tour_booking(request, booking_id):
    """Owner declines a pending tour booking with a reason."""
    booking = get_object_or_404(TourBooking, id=booking_id, tour__owner=request.user)
    
    if request.method == 'POST':
        if booking.status == 'pending':
            reason = request.POST.get('reason', '').strip()
            if not reason:
                reason = "The requested date is no longer available."
            
            booking.status = 'cancelled'
            booking.save()
            
            booking_reference = f"TV-{booking.id:04d}"
            send_booking_declined_email(booking, booking_reference, 'tour', reason)
            
            messages.success(request, f'Tour booking for {booking.guest.username} has been declined and they have been notified.')
            return redirect('owner_dashboard')
        else:
            messages.info(request, 'This booking cannot be declined.')
        
        return redirect('owner_dashboard')
    
    return redirect('owner_dashboard')


@login_required
def owner_tour_add(request):
    """Allows an owner to add a new tour."""
    if request.method == 'POST':
        form = TourManagementForm(request.POST)
        if form.is_valid():
            tour = form.save(commit=False)
            tour.owner = request.user
            tour.save()
            messages.success(request, f'"{tour.name}" by {tour.operator_name} has been successfully added!')
            return redirect('owner_dashboard')
    else:
        form = TourManagementForm()
        
    return render(request, 'dashboard/owner_tour_form.html', {
        'form': form,
        'title': 'Add New Tour'
    })


@login_required
def owner_tour_edit(request, tour_id):
    """Allows an owner to edit their existing tour."""
    tour = get_object_or_404(Tour, id=tour_id, owner=request.user)
    
    if request.method == 'POST':
        form = TourManagementForm(request.POST, instance=tour)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{tour.name}" by {tour.operator_name} has been updated successfully!')
            return redirect('owner_dashboard')
    else:
        form = TourManagementForm(instance=tour)
        
    return render(request, 'dashboard/owner_tour_form.html', {
        'form': form,
        'title': f'Edit: {tour.name}'
    })