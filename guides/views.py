from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from advisor.email_utils import (
    send_booking_confirmation_email, 
    send_booking_request_email, 
    send_booking_declined_email
)
from advisor.utils import get_booking_confirmation_message
from .forms import GuideBookingForm, GuideReviewForm, GuideManagementForm
from .models import Guide, GuideBooking, GuideReview


# ==========================================
# 1. GUIDE LISTING & DETAIL VIEWS
# ==========================================

def guide_list(request):
    """List all active local guides."""
    guides = Guide.objects.filter(is_active=True)
    
    search_query = request.GET.get('search', '').strip()
    
    if search_query:
        guides = guides.filter(
            Q(name__icontains=search_query) | 
            Q(bio__icontains=search_query) |
            Q(expertise__icontains=search_query)
        )
        
    return render(request, 'guides/guide_list.html', {
        'guides': guides,
        'search_query': search_query,
    })


def guide_detail(request, guide_id):
    """Detail page for a specific guide."""
    guide = get_object_or_404(Guide, id=guide_id, is_active=True)
    return render(request, 'guides/guide_detail.html', {'guide': guide})


# ==========================================
# 2. GUIDE BOOKING VIEWS (REQUEST & VERIFY)
# ==========================================

@login_required
def create_guide_booking(request, guide_id):
    """Handles the guide booking form submission - saves as PENDING for owner verification."""
    guide = get_object_or_404(Guide, id=guide_id, is_active=True)
    
    if request.method == 'POST':
        form = GuideBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.guide = guide
            booking.guest = request.user
            booking.status = 'pending'
            
            try:
                booking.full_clean()
                booking.save()
                
                booking_reference = f"VG-{booking.id:04d}"
                send_booking_request_email(booking, booking_reference, 'guide')
                
                # ✅ Clean, centralized UX message
                messages.success(request, get_booking_confirmation_message(booking, "Guide booking"))
                
                return redirect('guide_booking_request_received', booking_id=booking.id)
            except ValidationError as e:
                form.add_error(None, e.messages[0])
    else:
        form = GuideBookingForm()
    
    return render(request, 'guides/book_guide.html', {'form': form, 'guide': guide})


@login_required
def guide_booking_request_received(request, booking_id):
    """Displays a reassuring message that the guide request is being verified."""
    booking = get_object_or_404(GuideBooking, id=booking_id, guest=request.user)
    return render(request, 'guides/guide_booking_request_received.html', {'booking': booking})


@login_required
def guide_booking_confirmation(request, booking_id):
    """Display booking voucher for guide."""
    booking = get_object_or_404(GuideBooking, id=booking_id, guest=request.user)
    booking_reference = f"VG-{booking.id:04d}"
    
    return render(request, 'guides/guide_booking_confirmation.html', {
        'booking': booking,
        'booking_reference': booking_reference
    })


@login_required
def cancel_guide_booking(request, booking_id):
    """Allows a user to cancel a pending or confirmed guide booking."""
    booking = get_object_or_404(GuideBooking, id=booking_id, guest=request.user)
    
    if request.method == 'POST':
        if booking.status in ['pending', 'confirmed']:
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, 'Guide booking cancelled. Your spot has been released.')
        else:
            messages.info(request, 'This booking cannot be cancelled.')
        
        return redirect('guide_booking_confirmation', booking_id=booking.id)
    
    return render(request, 'guides/cancel_guide_booking.html', {'booking': booking})


# ==========================================
# 3. DASHBOARD VIEWS
# ==========================================

@login_required
def guide_bookings_dashboard(request):
    """Displays all guide bookings for the logged-in user."""
    today = timezone.now().date()
    
    all_bookings = GuideBooking.objects.filter(guest=request.user).select_related('guide')
    
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
    
    return render(request, 'guides/guide_bookings_dashboard.html', context)


# ==========================================
# 4. OWNER DASHBOARD ACTIONS (GUIDES)
# ==========================================

@login_required
def approve_guide_booking(request, booking_id):
    """Owner approves a pending guide booking."""
    booking = get_object_or_404(GuideBooking, id=booking_id, guide__owner=request.user)
    
    if booking.status == 'pending':
        booking.status = 'confirmed'
        booking.save()
        
        booking_reference = f"VG-{booking.id:04d}"
        send_booking_confirmation_email(booking, booking_reference, 'guide')
        
        messages.success(request, f'Guide booking for {booking.guest.username} has been confirmed and they have been notified!')
    else:
        messages.info(request, 'This booking cannot be approved.')
        
    return redirect('owner_dashboard')


@login_required
def decline_guide_booking(request, booking_id):
    """Owner declines a pending guide booking with a reason."""
    booking = get_object_or_404(GuideBooking, id=booking_id, guide__owner=request.user)
    
    if request.method == 'POST':
        if booking.status == 'pending':
            reason = request.POST.get('reason', '').strip()
            if not reason:
                reason = "The requested date is no longer available."
            
            booking.status = 'cancelled'
            booking.save()
            
            booking_reference = f"VG-{booking.id:04d}"
            send_booking_declined_email(booking, booking_reference, 'guide', reason)
            
            messages.success(request, f'Guide booking for {booking.guest.username} has been declined. The guest has been notified.')
        else:
            messages.info(request, 'This booking cannot be declined.')
        
        return redirect('owner_dashboard')
    
    return redirect('owner_dashboard')


@login_required
def owner_guide_add(request):
    """Allows an owner to add a new guide profile."""
    if request.method == 'POST':
        form = GuideManagementForm(request.POST)
        if form.is_valid():
            guide = form.save(commit=False)
            guide.owner = request.user
            guide.save()
            messages.success(request, f'Guide "{guide.name}" has been successfully added!')
            return redirect('owner_dashboard')
    else:
        form = GuideManagementForm()
        
    return render(request, 'dashboard/owner_guide_form.html', {
        'form': form,
        'title': 'Add New Guide Profile'
    })


@login_required
def owner_guide_edit(request, guide_id):
    """Allows an owner to edit their existing guide profile."""
    guide = get_object_or_404(Guide, id=guide_id, owner=request.user)
    
    if request.method == 'POST':
        form = GuideManagementForm(request.POST, instance=guide)
        if form.is_valid():
            form.save()
            messages.success(request, f'Guide "{guide.name}" has been updated successfully!')
            return redirect('owner_dashboard')
    else:
        form = GuideManagementForm(instance=guide)
        
    return render(request, 'dashboard/owner_guide_form.html', {
        'form': form,
        'title': f'Edit: {guide.name}'
    })