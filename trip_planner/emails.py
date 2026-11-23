from django.core.mail import send_mail, mail_admins
from django.conf import settings


# Your verified email in Resend (change this to your actual email)
ADMIN_EMAIL = 'sonnousith.tawon8@gmail.com'


def send_trip_plan_notifications(plan):
    """Send notification to admin + confirmation to visitor."""
    interests_display = {
        'adventure': '🏞️ Adventure',
        'motorbike': '🏍️ Motorbike/Buggy',
        'food': '🍜 Food & Culture',
        'relaxing': '🧘 Relaxing',
        'viewpoints': '📸 Viewpoints',
    }
    interests_text = ', '.join(
        interests_display.get(i, i) for i in plan.get_interests_list()
    )

    # ===== ADMIN NOTIFICATION =====
    admin_subject = f"🌟 New Trip Plan Request: {plan.name} ({plan.group_size} pax)"
    admin_message = (
        f"A new trip planning request has been submitted!\n\n"
        f"👤 Name: {plan.name}\n"
        f"📧 Email: {plan.email or 'Not provided'}\n"
        f"📱 WhatsApp: {plan.whatsapp or 'Not provided'}\n\n"
        f"📅 Travel Dates: {plan.travel_date_start} to {plan.travel_date_end}\n"
        f"👥 Group Size: {plan.group_size} people\n"
        f"✨ Interests: {interests_text}\n"
        f"💰 Budget: {plan.get_budget_display()}\n\n"
        f"📝 Special Requests:\n{plan.special_requests or 'None'}\n\n"
        f"---\n"
        f"Reply via WhatsApp: {plan.whatsapp or 'N/A'}\n"
        f"Reply via Email: {plan.email or 'N/A'}"
    )

    try:
        send_mail(
            subject=admin_subject,
            message=admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ADMIN_EMAIL],  # ✅ Send to your verified Gmail
            fail_silently=False,  # ✅ Show errors so we can debug
        )
        print(f"✅ Admin notification sent to {ADMIN_EMAIL}")
    except Exception as e:
        print(f"❌ Admin email failed: {e}")
        # Don't break the user experience if email fails
        raise

    # ===== VISITOR CONFIRMATION =====
    # Note: This will only work AFTER you verify vangviengstay.com in Resend
    if plan.email:
        visitor_subject = "We've received your Vang Vieng trip request! 🌟"
        visitor_message = (
            f"Hi {plan.name},\n\n"
            f"Thank you for reaching out! We've received your trip planning request "
            f"for {plan.travel_date_start} to {plan.travel_date_end} "
            f"({plan.group_size} travelers).\n\n"
            f"Our local team is crafting a personalized itinerary based on your "
            f"interests: {interests_text}.\n\n"
            f"We'll get back to you within 24 hours with a custom plan and pricing.\n\n"
            f"Need us sooner? Reply to this email or WhatsApp us directly.\n\n"
            f"See you in Vang Vieng! 🇱🇦\n"
            f"— The Vang Vieng Stay Team"
        )
        try:
            send_mail(
                subject=visitor_subject,
                message=visitor_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[plan.email],
                fail_silently=True,  # Keep silent for visitor emails (domain not verified yet)
            )
            print(f"✅ Visitor confirmation sent to {plan.email}")
        except Exception as e:
            print(f"⚠️ Visitor email failed (expected until domain is verified): {e}")