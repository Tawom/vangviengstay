from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Inquiry(models.Model):
    SUBJECT_CHOICES = [
        ('general', _('General Question')),
        ('booking', _('Booking Inquiry')),
        ('guesthouse', _('Guesthouse')),
        ('tour', _('Tour')),
        ('motorbike', _('Motorbike Rental')),
        ('buggy', _('Buggy Car Rental')),
        ('guide', _('Local Guide')),
        ('support', _('Technical Support')),
        ('other', _('Other')),
    ]

    STATUS_CHOICES = [
        ('new', _('New')),
        ('read', _('Read')),
        ('responded', _('Responded')),
        ('closed', _('Closed')),
    ]

    name = models.CharField(max_length=200, verbose_name=_('Name'))
    email = models.EmailField(verbose_name=_('Email'))
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name=_('Phone'))
    subject = models.CharField(max_length=30, choices=SUBJECT_CHOICES, default='general', verbose_name=_('Subject'))
    message = models.TextField(verbose_name=_('Message'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name=_('Status'))

    # Track if emails were sent successfully
    customer_email_sent = models.BooleanField(default=False, verbose_name=_('Customer Email Sent'))
    admin_email_sent = models.BooleanField(default=False, verbose_name=_('Admin Email Sent'))

    # Admin reply tracking
    admin_reply = models.TextField(blank=True, verbose_name=_('Admin Reply'))
    replied_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Replied At'))
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='replied_inquiries',
        verbose_name=_('Replied By'),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Inquiry')
        verbose_name_plural = _('Inquiries')

    def __str__(self):
        return f"{self.name} - {self.get_subject_display()} ({self.get_status_display()})"