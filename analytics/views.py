from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .models import DailyVisit, PageVisit


@staff_member_required
def analytics_dashboard(request):
    """Admin-only analytics dashboard."""
    today = timezone.now().date()
    
    # Today's stats
    today_stats = DailyVisit.objects.filter(date=today).first()
    
    # Last 7 days
    last_7_days = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        stats = DailyVisit.objects.filter(date=date).first()
        last_7_days.append({
            'date': date.strftime('%a'),
            'visits': stats.total_visits if stats else 0,
            'unique': stats.unique_visitors if stats else 0,
        })
    
    # Last 30 days total
    thirty_days_ago = today - timedelta(days=30)
    monthly_stats = DailyVisit.objects.filter(
        date__gte=thirty_days_ago
    ).aggregate(
        total_visits=Sum('total_visits'),
        total_unique=Sum('unique_visitors')
    )
    
    # Top pages (last 7 days)
    seven_days_ago = today - timedelta(days=7)
    top_pages = PageVisit.objects.filter(
        date__gte=seven_days_ago
    ).values('path').annotate(
        total_visits=Sum('visit_count')
    ).order_by('-total_visits')[:10]
    
    context = {
        'title': 'Site Analytics',
        'today_stats': today_stats,
        'last_7_days': last_7_days,
        'monthly_stats': monthly_stats,
        'top_pages': top_pages,
    }
    
    return render(request, 'admin/analytics_dashboard.html', context)