def get_booking_confirmation_message(booking, booking_type="Booking"):
    """
    Returns the appropriate confirmation message based on whether
    the guest provided a phone number.
    """
    if hasattr(booking, 'guest_phone') and booking.guest_phone:
        return f'{booking_type} request received! The operator is verifying availability. You will receive a final confirmation via WhatsApp to {booking.guest_phone} shortly.'
    else:
        return f'{booking_type} request received! The operator is verifying availability. You will receive a final confirmation email shortly.'
