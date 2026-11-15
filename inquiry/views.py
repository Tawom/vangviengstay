from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import InquiryForm
from advisor.email_utils import send_inquiry_confirmation_email, send_inquiry_notification_email


def inquiry_view(request):
    """Handle customer inquiry form submission."""
    if request.method == 'POST':
        form = InquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save()
            
            # Send both emails
            send_inquiry_confirmation_email(inquiry)
            send_inquiry_notification_email(inquiry)
            
            messages.success(
                request, 
                'Thank you! Your inquiry has been received. We will email you back within 24 hours.'
            )
            return redirect('inquiry_success')
    else:
        form = InquiryForm()
    
    return render(request, 'inquiry/inquiry.html', {'form': form})


def inquiry_success(request):
    """Display success page after inquiry submission."""
    return render(request, 'inquiry/inquiry_success.html')