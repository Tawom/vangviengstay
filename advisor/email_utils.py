from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def send_booking_request_email(booking, booking_reference, booking_type='guesthouse'):
    """
    Send a booking REQUEST email to the guest (Pending Verification).
    This is triggered immediately when the guest submits the booking form.
    """
    if booking_type == 'guesthouse':
        voucher_url = f"{settings.SITE_URL}/booking/{booking.id}/request-received/"
        subject_prefix = "Booking Request Received"
        name = booking.guesthouse.name
    elif booking_type == 'tour':
        voucher_url = f"{settings.SITE_URL}/tours/booking/{booking.id}/request-received/"
        subject_prefix = "Tour Booking Request Received"
        name = booking.tour.name
    elif booking_type == 'guide':
        voucher_url = f"{settings.SITE_URL}/guides/booking/{booking.id}/request-received/"
        subject_prefix = "Guide Booking Request Received"
        name = booking.guide.name
    elif booking_type == 'motorbike':
        voucher_url = f"{settings.SITE_URL}/motorbike/booking/{booking.id}/request-received/"
        subject_prefix = "Motorbike Rental Request Received"
        name = booking.motorbike.name
    elif booking_type == 'buggy':
        voucher_url = f"{settings.SITE_URL}/buggy/booking/{booking.id}/request-received/"
        subject_prefix = "Buggy Booking Request Received"
        name = booking.buggy_car.name
    else:
        voucher_url = f"{settings.SITE_URL}/"
        subject_prefix = "Booking Request Received"
        name = "your booking"

    subject = f"{subject_prefix}: {name} - Ref: {booking_reference}"
    
    # Render HTML email (The template dynamically checks if status == 'pending')
    html_message = render_to_string('emails/booking_confirmation.html', {
        'booking': booking,
        'booking_reference': booking_reference,
        'booking_type': booking_type,
        'voucher_url': voucher_url,
    })
    
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.guest.email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"✅ Booking request email sent to {booking.guest.email}")
        return True
    except Exception as e:
        print(f"❌ Error sending booking request email: {e}")
        return False


def send_booking_confirmation_email(booking, booking_reference, booking_type='guesthouse'):
    """
    Send a final booking CONFIRMATION email to the guest.
    This should be triggered when the owner/admin approves the pending booking.
    """
    if booking_type == 'guesthouse':
        voucher_url = f"{settings.SITE_URL}/booking/{booking.id}/confirmation/"
        subject_prefix = "Booking Confirmed"
        name = booking.guesthouse.name
    elif booking_type == 'tour':
        voucher_url = f"{settings.SITE_URL}/tours/booking/{booking.id}/confirmation/"
        subject_prefix = "Tour Booking Confirmed"
        name = booking.tour.name
    elif booking_type == 'guide':
        voucher_url = f"{settings.SITE_URL}/guides/booking/{booking.id}/confirmation/"
        subject_prefix = "Guide Booking Confirmed"
        name = booking.guide.name
    elif booking_type == 'motorbike':
        voucher_url = f"{settings.SITE_URL}/motorbike/booking/{booking.id}/confirmation/"
        subject_prefix = "Motorbike Rental Confirmed"
        name = booking.motorbike.name
    elif booking_type == 'buggy':
        voucher_url = f"{settings.SITE_URL}/buggy/booking/{booking.id}/confirmation/"
        subject_prefix = "Buggy Booking Confirmed"
        name = booking.buggy_car.name
    else:
        voucher_url = f"{settings.SITE_URL}/"
        subject_prefix = "Booking Confirmed"
        name = "your booking"

    subject = f"{subject_prefix}: {name} - Ref: {booking_reference}"
    
    # Render HTML email (The template dynamically checks if status == 'confirmed')
    html_message = render_to_string('emails/booking_confirmation.html', {
        'booking': booking,
        'booking_reference': booking_reference,
        'booking_type': booking_type,
        'voucher_url': voucher_url,
    })
    
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.guest.email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"✅ Booking confirmation email sent to {booking.guest.email}")
        return True
    except Exception as e:
        print(f"❌ Error sending booking confirmation email: {e}")
        return False


def send_contact_form_email(name, email, subject, message):
    """
    Send contact form submission to site admin AND an auto-response to the user.
    """
    admin_success = False
    user_success = False

    # 1. Send email to site admin
    admin_html_message = render_to_string('emails/contact_notification.html', {
        'name': name,
        'email': email,
        'subject': subject,
        'message': message,
    })
    admin_plain_message = strip_tags(admin_html_message)
    
    try:
        send_mail(
            subject=f"[Contact Form] {subject}",
            message=admin_plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['sonnousith.tawon8@gmail.com'],  # Replace with your actual admin email
            html_message=admin_html_message,
            fail_silently=False,
        )
        print(f"✅ Contact form email sent to admin")
        admin_success = True
    except Exception as e:
        print(f"❌ Error sending contact form to admin: {e}")
    
    # 2. Send auto-response to the user
    auto_response_html = render_to_string('emails/contact_auto_response.html', {
        'name': name,
        'subject': subject,
        'message': message,
        'site_url': settings.SITE_URL,
    })
    auto_response_plain = strip_tags(auto_response_html)
    
    try:
        send_mail(
            subject="Thank you for contacting Vang Vieng Stay - We received your message",
            message=auto_response_plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],  # Send back to the user
            html_message=auto_response_html,
            fail_silently=False,
        )
        print(f"✅ Auto-response email sent to {email}")
        user_success = True
    except Exception as e:
        print(f"❌ Error sending auto-response to user: {e}")
    
    # Return True if the admin received the message (most critical), 
    # even if the user's auto-response failed for some reason.
    return admin_success


def send_booking_declined_email(booking, booking_reference, booking_type='guesthouse', reason=''):
    """
    Send a booking DECLINED email to the guest with the reason.
    Triggered when the owner declines a pending booking.
    """
    if booking_type == 'guesthouse':
        subject = f"Booking Request Declined: {booking.guesthouse.name} - Ref: {booking_reference}"
        property_name = booking.guesthouse.name
        property_type = 'guesthouse'
    elif booking_type == 'tour':
        subject = f"Tour Request Declined: {booking.tour.name} - Ref: {booking_reference}"
        property_name = booking.tour.name
        property_type = 'tour'
    elif booking_type == 'guide':
        subject = f"Guide Request Declined: {booking.guide.name} - Ref: {booking_reference}"
        property_name = booking.guide.name
        property_type = 'guide'
    elif booking_type == 'motorbike':
        subject = f"Motorbike Request Declined: {booking.motorbike.name} - Ref: {booking_reference}"
        property_name = booking.motorbike.name
        property_type = 'motorbike'
    elif booking_type == 'buggy':
        subject = f"Buggy Request Declined: {booking.buggy_car.name} - Ref: {booking_reference}"
        property_name = booking.buggy_car.name
        property_type = 'buggy'
    else:
        subject = f"Booking Request Declined - Ref: {booking_reference}"
        property_name = "your booking"
        property_type = 'guesthouse'
    
    # Default reasons if none provided
    if not reason:
        reason = "The requested dates are no longer available."
    
    html_message = render_to_string('emails/booking_declined.html', {
        'booking': booking,
        'booking_reference': booking_reference,
        'booking_type': booking_type,
        'property_name': property_name,
        'property_type': property_type,
        'reason': reason,
    })
    
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.guest.email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"✅ Booking declined email sent to {booking.guest.email}")
        return True
    except Exception as e:
        print(f"❌ Error sending booking declined email: {e}")
        return False