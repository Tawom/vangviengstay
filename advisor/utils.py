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