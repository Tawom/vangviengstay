from django.db import models

class DailyVisit(models.Model):
    """Tracks daily site-wide visitor statistics."""
    date = models.DateField(unique=True, db_index=True)
    total_visits = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Daily Visit'
        verbose_name_plural = 'Daily Visits'
    
    def __str__(self):
        return f"{self.date}: {self.total_visits} visits ({self.unique_visitors} unique)"


class PageVisit(models.Model):
    """Tracks daily visits to specific pages."""
    date = models.DateField(db_index=True)
    path = models.CharField(max_length=500, db_index=True)
    visit_count = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('date', 'path')
        ordering = ['-date', '-visit_count']
        verbose_name = 'Page Visit'
        verbose_name_plural = 'Page Visits'
    
    def __str__(self):
        return f"{self.date}: {self.path} ({self.visit_count} visits)"


# ✅ NEW: Tracks individual visit details for deep analytics
class VisitLog(models.Model):
    """Records every individual visit with IP, device, and timestamp."""
    path = models.CharField(max_length=500, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    is_unique = models.BooleanField(default=False, help_text="True if this IP hasn't visited today")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Visit Log'
        verbose_name_plural = 'Visit Logs'

    def __str__(self):
        return f"{self.path} | {self.ip_address} | {self.timestamp.strftime('%Y-%m-%d %H:%M')}"