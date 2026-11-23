from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import TripPlanForm
from .emails import send_trip_plan_notifications


def trip_plan(request):
    if request.method == 'POST':
        form = TripPlanForm(request.POST)
        if form.is_valid():
            plan = form.save()
            try:
                send_trip_plan_notifications(plan)
            except Exception as e:
                # Don't break the user experience if email fails
                print(f"Email notification failed: {e}")
            messages.success(request, "Your trip request has been received!")
            return redirect('trip_plan_success')
    else:
        form = TripPlanForm()

    return render(request, 'trip_planner/trip_plan.html', {'form': form})


def trip_plan_success(request):
    return render(request, 'trip_planner/trip_plan_success.html')