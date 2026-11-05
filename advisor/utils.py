import urllib.parse


def get_booking_confirmation_message(booking, booking_type="Booking"):
    """
    Generates a smart, conditional success message for booking requests.
    If a phone number is provided, it mentions WhatsApp.
    Otherwise, it gracefully skips the WhatsApp sentence to avoid awkward cutoffs.
    """
    # Safely get phone number (checks Booking model, then Guest/User model)
    phone = (
        getattr(booking, 'guest_phone', None) or 
        getattr(booking, 'phone', None) or 
        getattr(booking.guest, 'phone', None)
    )
    
    # Safely get email
    email = getattr(booking.guest, 'email', 'your registered email')
    
    if phone:
        return (
            f"{booking_type} request received! The operator is verifying availability. "
            f"You will receive a quick update via WhatsApp to {phone} shortly, "
            f"and an official booking voucher will be sent to {email} once confirmed."
        )
    else:
        return (
            f"{booking_type} request received! The operator is verifying availability. "
            f"An official booking voucher will be sent to {email} once confirmed."
        )


def get_whatsapp_link(booking, booking_type="booking"):
    """
    Generate a WhatsApp click-to-chat link with a pre-filled confirmation message.
    Returns None if no phone number is found.
    """
    # Safely get phone number from multiple possible locations
    phone = (
        getattr(booking, 'guest_phone', None) or 
        getattr(booking, 'phone', None) or 
        getattr(booking.guest, 'phone', None) or
        (hasattr(booking.guest, 'profile') and getattr(booking.guest.profile, 'phone_number', None))
    )
    
    if not phone:
        return None
    
    # Clean the phone number (remove +, spaces, dashes, parentheses)
    phone = ''.join(c for c in str(phone) if c.isdigit())
    
    # Convert Laos local format (020...) to international (85620...)
    if phone.startswith('0') and not phone.startswith('00'):
        phone = '856' + phone[1:]
    
    # Skip if phone is too short to be valid
    if len(phone) < 8:
        return None
    
    # Build the pre-filled message
    guest_name = f"{booking.guest.first_name} {booking.guest.last_name}".strip() or booking.guest.username
    
    # Get service name and date based on booking type
    service_name = ""
    booking_date = ""
    
    if booking_type == "tour":
        service_name = booking.tour.name
        booking_date = booking.booking_date.strftime('%d %b %Y') if booking.booking_date else ''
    elif booking_type == "guesthouse":
        service_name = booking.guesthouse.name
        booking_date = f"{booking.check_in.strftime('%d %b')} - {booking.check_out.strftime('%d %b %Y')}" if booking.check_in else ''
    elif booking_type == "motorbike":
        service_name = booking.motorbike.name
        booking_date = f"{booking.start_date.strftime('%d %b')} - {booking.end_date.strftime('%d %b %Y')}" if booking.start_date else ''
    elif booking_type == "buggy":
        service_name = booking.buggy_car.name
        booking_date = booking.booking_date.strftime('%d %b %Y') if booking.booking_date else ''
    elif booking_type == "guide":
        service_name = booking.guide.name
        booking_date = booking.booking_date.strftime('%d %b %Y') if booking.booking_date else ''
    
    reference = f"{booking_type.upper()[:2]}-{booking.id:04d}"
    
    message = (
        f"Hello {guest_name}! 🎉\n\n"
        f"Great news - your {booking_type} booking is confirmed!\n\n"
        f"📋 Reference: {reference}\n"
        f"📍 Service: {service_name}\n"
        f"📅 Date: {booking_date}\n\n"
        f"If you have any questions, just reply here. See you soon!\n\n"
        f"- Vang Vieng Stay Team\n"
        f"🌐 vangviengstay.com"
    )
    
    # URL encode the message
    encoded_message = urllib.parse.quote(message)
    
    return f"https://wa.me/{phone}?text={encoded_message}"