from django.db import models


class Inquiry(models.Model):
    SUBJECT_CHOICES = [
        ('general', 'General Question'),
        ('booking', 'Booking Inquiry'),
        ('guesthouse', 'Guesthouse'),
        ('tour', 'Tour'),
        ('motorbike', 'Motorbike Rental'),
        ('buggy', 'Buggy Car Rental'),
        ('guide', 'Local Guide'),
        ('support', 'Technical Support'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('responded', 'Responded'),
        ('closed', 'Closed'),
    ]
    
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True, null=True)
    subject = models.CharField(max_length=30, choices=SUBJECT_CHOICES, default='general')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    
    # Track if emails were sent successfully
    customer_email_sent = models.BooleanField(default=False)
    admin_email_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_subject_display()} ({self.status})"