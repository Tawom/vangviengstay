from datetime import date, timedelta, datetime

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q, Min, Max, Avg
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import get_language

from accounts.models import EmailVerificationToken, Profile
from .models import Booking, Guesthouse, GuesthouseReview

from tours.models import Tour, TourBooking, TourReview
from guides.models import Guide, GuideBooking, GuideReview
from motorbike.models import Motorbike, MotorbikeBooking, MotorbikeReview
from buggy.models import BuggyCar, BuggyCarBooking, BuggyCarReview

from advisor.email_utils import (
    send_booking_confirmation_email, 
    send_contact_form_email, 
    send_booking_request_email,
    send_booking_declined_email
)
from advisor.utils import get_booking_confirmation_message
from .forms import (
    BookingForm, 
    GuesthouseReviewForm, 
    GuesthouseManagementForm,
    EmailSignupForm,
    PhoneSignupForm
)


# ==========================================
# 1. GUESTHOUSE LISTING & DETAIL VIEWS
# ==========================================

def guesthouse_list(request):
    """Home page: Lists all active guesthouses with advanced search and filtering."""
    guesthouses = Guesthouse.objects.filter(is_active=True)
    
    search_query = request.GET.get('search', '').strip()
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')
    guests = request.GET.get('guests', '1')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    city = request.GET.get('city', '')
    
    if search_query:
        guesthouses = guesthouses.filter(
            Q(name__icontains=search_query) | 
            Q(city__icontains=search_query) |
            Q(description_en__icontains=search_query) |
            Q(description_lo__icontains=search_query)
        )
    
    if city:
        guesthouses = guesthouses.filter(city__iexact=city)
    
    if min_price:
        try:
            guesthouses = guesthouses.filter(price_per_night__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            guesthouses = guesthouses.filter(price_per_night__lte=float(max_price))
        except ValueError:
            pass
    
    if check_in and check_out:
        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
            
            unavailable_ids = Booking.objects.filter(
                status__in=['pending', 'confirmed'],
                check_in__lt=check_out_date,
                check_out__gt=check_in_date
            ).values_list('guesthouse_id', flat=True).distinct()
            
            guesthouses = guesthouses.exclude(pk__in=unavailable_ids)
        except ValueError:
            pass
    
    available_cities = Guesthouse.objects.filter(is_active=True).values_list('city', flat=True).distinct().order_by('city')
    
    price_stats = Guesthouse.objects.filter(is_active=True).aggregate(
        min_price=Min('price_per_night'),
        max_price=Max('price_per_night')
    )
    
    total_listings = (
        Guesthouse.objects.filter(is_active=True).count() +
        Tour.objects.filter(is_active=True).count() +
        Guide.objects.filter(is_active=True).count() +
        Motorbike.objects.filter(is_active=True).count() +
        BuggyCar.objects.filter(is_active=True).count()
    )

    total_travelers = (
        Booking.objects.filter(status__in=['confirmed', 'completed']).count() +
        TourBooking.objects.filter(status__in=['confirmed', 'completed']).count() +
        GuideBooking.objects.filter(status__in=['confirmed', 'completed']).count() +
        MotorbikeBooking.objects.filter(status__in=['confirmed', 'completed']).count() +
        BuggyCarBooking.objects.filter(status__in=['confirmed', 'completed']).count()
    )

    review_models = [GuesthouseReview, TourReview, GuideReview, MotorbikeReview, BuggyCarReview]
    all_ratings = []
    total_reviews = 0
    
    for model in review_models:
        agg = model.objects.aggregate(Avg('rating'))
        if agg['rating__avg']:
            all_ratings.append(agg['rating__avg'])
        total_reviews += model.objects.count()
    
    overall_rating = round(sum(all_ratings) / len(all_ratings), 1) if all_ratings else 4.9
    
    context = {
        'guesthouses': guesthouses,
        'search_query': search_query,
        'check_in': check_in,
        'check_out': check_out,
        'guests': guests,
        'min_price': min_price or price_stats['min_price'],
        'max_price': max_price or price_stats['max_price'],
        'selected_city': city,
        'available_cities': available_cities,
        'price_range': {
            'min': int(price_stats['min_price'] or 0),
            'max': int(price_stats['max_price'] or 100)
        },
        'total_listings': total_listings,
        'total_travelers': total_travelers,
        'overall_rating': overall_rating,
        'total_reviews': total_reviews,
    }
    
    return render(request, 'guesthouse/guesthouse_list.html', context)


def guesthouse_detail(request, guesthouse_id):
    """Detail page: Shows guesthouse info and 30-day availability calendar."""
    guesthouse = get_object_or_404(Guesthouse, pk=guesthouse_id, is_active=True)
    
    today = date.today()
    availability_schedule = []
    
    upcoming_bookings = Booking.objects.filter(
        guesthouse=guesthouse,
        status__in=['pending', 'confirmed'],
        check_out__gte=today 
    )
    
    for i in range(30):
        current_day = today + timedelta(days=i)
        is_available = True
        
        for booking in upcoming_bookings:
            if booking.check_in <= current_day < booking.check_out:
                is_available = False
                break
                
        availability_schedule.append({
            'date': current_day,
            'is_available': is_available,
            'day_name': current_day.strftime('%a'), 
            'day_num': current_day.day               
        })
        
    current_lang = getattr(request, 'LANGUAGE_CODE', 'en')
    desc_text = guesthouse.get_description(current_lang)
    desc_snippet = desc_text[:150] + "..." if desc_text else "Book the best guesthouse in Vang Vieng, Laos."
    
    context = {
        'guesthouse': guesthouse,
        'availability': availability_schedule,
        'meta_title': f"{guesthouse.name} - Vang Vieng Stay",
        'meta_description': desc_snippet,
        'meta_image': guesthouse.main_image_url if guesthouse.main_image_url else 'https://vangviengstay.com/static/images/og-default.jpg',
        'meta_url': request.build_absolute_uri(),
        'meta_type': 'article',
    }
    
    return render(request, 'guesthouse/guesthouse_detail.html', context)


# ==========================================
# 2. BOOKING & PAYMENT VIEWS
# ==========================================

@login_required
def create_booking(request, guesthouse_id):
    """Handles the booking form submission - saves as PENDING for owner verification."""
    guesthouse = get_object_or_404(Guesthouse, pk=guesthouse_id, is_active=True)
    
    if request.method == 'POST':
        form = BookingForm(request.POST, guesthouse=guesthouse)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.guesthouse = guesthouse
            booking.guest = request.user
            booking.status = 'pending'
            
            if request.user.email and not booking.contact_email:
                booking.contact_email = request.user.email
            
            try:
                booking.full_clean()
                booking.save()
                
                booking_reference = f"VV-{booking.pk:04d}"
                send_booking_request_email(booking, booking_reference, 'guesthouse')
                
                messages.success(request, get_booking_confirmation_message(booking, "Booking"))
                return redirect('booking_request_received', booking_id=booking.pk)
            except ValidationError as e:
                form.add_error(None, e.messages[0])
    else:
        form = BookingForm(guesthouse=guesthouse)
        if request.user.is_authenticated and request.user.email:
            form.fields['contact_email'].initial = request.user.email
        
    return render(request, 'guesthouse/book.html', {'form': form, 'guesthouse': guesthouse})


@login_required
def booking_request_received(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, guest=request.user)
    return render(request, 'guesthouse/booking_request_received.html', {'booking': booking})


@login_required
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, guest=request.user)
    booking_reference = f"VV-{booking.pk:04d}"
    
    return render(request, 'guesthouse/booking_confirmation.html', {
        'booking': booking,
        'booking_reference': booking_reference
    })


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, guest=request.user)
    
    if request.method == 'POST':
        if booking.status in ['pending', 'confirmed']:
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, 'Booking cancelled. Your dates have been released.')
        else:
            messages.info(request, 'This booking cannot be cancelled.')
            
        return redirect('booking_confirmation', booking_id=booking.pk)
        
    return render(request, 'guesthouse/cancel_booking.html', {'booking': booking})


# ==========================================
# 3. DASHBOARD & USER MANAGEMENT VIEWS
# ==========================================

@login_required
def guesthouse_bookings_dashboard(request):
    today = timezone.now().date()
    
    all_bookings = Booking.objects.filter(guest=request.user).select_related('guesthouse')
    
    upcoming_bookings = all_bookings.filter(
        check_out__gte=today,
        status__in=['pending', 'confirmed']
    ).order_by('check_in')
    
    cancelled_bookings = all_bookings.filter(
        status__in=['cancelled', 'refunded']
    ).order_by('-created_at')
    
    past_bookings = all_bookings.filter(
        check_out__lt=today,
        status__in=['pending', 'confirmed', 'completed']
    ).order_by('-check_in')
    
    context = {
        'upcoming_bookings': upcoming_bookings,
        'cancelled_bookings': cancelled_bookings,
        'past_bookings': past_bookings,
        'total_bookings': all_bookings.count(),
    }
    
    return render(request, 'guesthouse/guesthouse_bookings_dashboard.html', context)


@login_required
def universal_dashboard(request):
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
# 3b. SIGNUP & VERIFICATION VIEWS
# ==========================================

def signup_choice(request):
    """Displays options to sign up via Email or Phone."""
    return render(request, 'guesthouse/signup_choice.html')


def signup_email(request):
    """User registration with email and verification."""
    if request.method == 'POST':
        form = EmailSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            profile, created = Profile.objects.get_or_create(user=user)
            profile.email_verified = False
            profile.save()
            
            owner_group, created = Group.objects.get_or_create(name='Owner')
            user.groups.add(owner_group)
            
            token = EmailVerificationToken.objects.create(user=user)
            
            verification_link = f"{request.scheme}://{request.get_host()}/accounts/verify-email/{token.token}/"
            send_mail(
                subject='Verify your email - Vang Vieng Stay',
                message=(
                    f'Hi {user.username},\n\n'
                    f'Please click the link below to verify your email:\n\n'
                    f'{verification_link}\n\n'
                    f'This link will expire in 24 hours.\n\n'
                    f'Thank you!'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Please check your email to verify your account.')
            messages.warning(request, '⚠️ Please verify your email to unlock all dashboard features.')
            return redirect('owner_dashboard')
    else:
        form = EmailSignupForm()
    
    return render(request, 'guesthouse/signup_email.html', {'form': form})


def verify_email(request, token):
    """Verify user's email address using the token from the email link."""
    try:
        verification_token = EmailVerificationToken.objects.get(token=token, is_used=False)
        
        if verification_token.is_expired:
            messages.error(request, 'This verification link has expired. Please request a new one.')
            return redirect('login')
        
        profile, created = Profile.objects.get_or_create(user=verification_token.user)
        profile.email_verified = True
        profile.save()
        
        verification_token.is_used = True
        verification_token.save()
        
        messages.success(request, '✅ Your email has been verified successfully!')
        return redirect('owner_dashboard')
        
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'Invalid or already used verification link.')
        return redirect('login')


@login_required
def resend_verification(request):
    """Resend verification email to the logged-in user."""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if profile.email_verified:
        messages.info(request, 'Your email is already verified!')
        return redirect('owner_dashboard')
    
    if not request.user.email:
        messages.error(request, 'No email address found on your account. Please update your profile.')
        return redirect('owner_dashboard')
    
    EmailVerificationToken.objects.filter(user=request.user, is_used=False).delete()
    token = EmailVerificationToken.objects.create(user=request.user)
    
    verification_link = f"{request.scheme}://{request.get_host()}/accounts/verify-email/{token.token}/"
    send_mail(
        subject='Verify your email - Vang Vieng Stay',
        message=(
            f'Hi {request.user.username},\n\n'
            f'You requested a new verification link. Please click below:\n\n'
            f'{verification_link}\n\n'
            f'This link will expire in 24 hours.\n\n'
            f'Thank you!'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.user.email],
        fail_silently=False,
    )
    
    messages.success(request, '✅ A new verification email has been sent! Please check your inbox (and spam folder).')
    return redirect('owner_dashboard')


def signup_phone(request):
    """User registration with phone number."""
    if request.method == 'POST':
        form = PhoneSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            owner_group, created = Group.objects.get_or_create(name='Owner')
            user.groups.add(owner_group)
            
            phone_number = form.cleaned_data.get('phone_number')
            if phone_number and hasattr(user, 'profile'):
                user.profile.phone_number = phone_number
                user.profile.phone_verified = False
                user.profile.save()
            
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created with phone.')
            messages.info(request, '📱 OTP verification for your phone number will be available soon.')
            return redirect('owner_dashboard')
    else:
        form = PhoneSignupForm()
    
    return render(request, 'guesthouse/signup_phone.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'tour_list')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    
    return render(request, 'guesthouse/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('tour_list')


# ==========================================
# 4. OWNER DASHBOARD & MANAGEMENT VIEWS
# ==========================================

@login_required
def owner_dashboard(request):
    if not request.user.groups.filter(name='Owner').exists() and not request.user.is_superuser:
        messages.warning(request, "You do not have owner permissions.")
        return redirect('tour_list')
        
    my_guesthouses = Guesthouse.objects.filter(owner=request.user)
    
    pending_bookings = Booking.objects.filter(
        guesthouse__owner=request.user,
        status='pending'
    ).select_related('guesthouse', 'guest').order_by('-created_at')
    
    context = {
        'my_guesthouses': my_guesthouses,
        'total_properties': my_guesthouses.count(),
        'active_properties': my_guesthouses.filter(is_active=True).count(),
        'pending_bookings': pending_bookings,
    }
    return render(request, 'dashboard/owner_dashboard.html', context)


@login_required
def owner_guesthouse_add(request):
    if request.method == 'POST':
        form = GuesthouseManagementForm(request.POST)
        if form.is_valid():
            guesthouse = form.save(commit=False)
            guesthouse.owner = request.user
            guesthouse.save()
            messages.success(request, f'"{guesthouse.name}" has been successfully added!')
            return redirect('owner_dashboard')
    else:
        form = GuesthouseManagementForm()
        
    return render(request, 'dashboard/owner_guesthouse_form.html', {
        'form': form,
        'title': 'Add New Guesthouse'
    })


@login_required
def owner_guesthouse_edit(request, pk):
    guesthouse = get_object_or_404(Guesthouse, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        form = GuesthouseManagementForm(request.POST, instance=guesthouse)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{guesthouse.name}" has been updated successfully!')
            return redirect('owner_dashboard')
    else:
        form = GuesthouseManagementForm(instance=guesthouse)
        
    return render(request, 'dashboard/owner_guesthouse_form.html', {
        'form': form,
        'title': f'Edit: {guesthouse.name}'
    })


@login_required
def approve_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, guesthouse__owner=request.user)
    
    if booking.status == 'pending':
        booking.status = 'confirmed'
        booking.save()
        
        booking_reference = f"VV-{booking.pk:04d}"
        send_booking_confirmation_email(booking, booking_reference, 'guesthouse')
        
        messages.success(request, f'Booking for {booking.guest.username} has been confirmed and they have been notified!')
    else:
        messages.info(request, 'This booking cannot be approved.')
        
    return redirect('owner_dashboard')


@login_required
def decline_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, guesthouse__owner=request.user)
    
    if request.method == 'POST':
        if booking.status == 'pending':
            reason = request.POST.get('reason', '').strip()
            if not reason:
                reason = "The requested dates are no longer available."
            
            booking.status = 'cancelled'
            booking.save()
            
            booking_reference = f"VV-{booking.pk:04d}"
            send_booking_declined_email(booking, booking_reference, 'guesthouse', reason)
            
            messages.success(request, f'Booking for {booking.guest.username} has been declined. The guest has been notified.')
        else:
            messages.info(request, 'This booking cannot be declined.')
        
        return redirect('owner_dashboard')
    
    return redirect('owner_dashboard')


# ==========================================
# 5. SUPPORT & REVIEW VIEWS
# ==========================================

def terms_of_service(request):
    return render(request, 'guesthouse/terms_of_service.html')


@login_required
def submit_guesthouse_review(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, guest=request.user)
    
    if booking.status != 'confirmed':
        messages.error(request, 'You can only review confirmed bookings.')
        return redirect('guesthouse_bookings_dashboard')
        
    if booking.check_out >= timezone.now().date():
        messages.error(request, 'You can only leave a review after your stay has ended.')
        return redirect('guesthouse_bookings_dashboard')
        
    if hasattr(booking, 'guesthouse_review'):
        messages.info(request, 'You have already reviewed this guesthouse.')
        return redirect('guesthouse_bookings_dashboard')

    if request.method == 'POST':
        form = GuesthouseReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.guesthouse = booking.guesthouse
            review.guest = request.user
            review.save()
            messages.success(request, 'Thank you for your review!')
            return redirect('guesthouse_detail', guesthouse_id=booking.guesthouse.pk)
    else:
        form = GuesthouseReviewForm()

    return render(request, 'guesthouse/submit_review.html', {
        'form': form,
        'booking': booking
    })


@login_required
def edit_guesthouse_review(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, guest=request.user)
    
    if not hasattr(booking, 'guesthouse_review'):
        messages.error(request, 'No review found for this booking.')
        return redirect('guesthouse_bookings_dashboard')
    
    review = booking.guesthouse_review

    if request.method == 'POST':
        form = GuesthouseReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your review has been updated!')
            return redirect('guesthouse_detail', guesthouse_id=booking.guesthouse.pk)
    else:
        form = GuesthouseReviewForm(instance=review)

    return render(request, 'guesthouse/edit_review.html', {
        'form': form,
        'booking': booking,
        'review': review
    })


@login_required
def delete_guesthouse_review(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, guest=request.user)
    
    if not hasattr(booking, 'guesthouse_review'):
        messages.error(request, 'No review found for this booking.')
        return redirect('guesthouse_bookings_dashboard')
    
    review = booking.guesthouse_review

    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Your review has been deleted.')
        return redirect('guesthouse_bookings_dashboard')
    
    return render(request, 'guesthouse/confirm_delete_review.html', {
        'booking': booking,
        'review': review
    })