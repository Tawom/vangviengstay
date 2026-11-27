from django.conf import settings
from django.db import models
from django.template import Context, Template
from django.utils.translation import gettext_lazy as _


class EmailSignature(models.Model):
    name = models.CharField(max_length=120, verbose_name=_('Signature Name'))
    sender_name = models.CharField(max_length=120, verbose_name=_('Sender Name'))
    sender_title = models.CharField(max_length=120, blank=True, verbose_name=_('Sender Title'))
    email = models.EmailField(verbose_name=_('Reply/Contact Email'))
    phone = models.CharField(max_length=40, blank=True, verbose_name=_('Phone'))
    website_url = models.URLField(blank=True, verbose_name=_('Website URL'))
    avatar_url = models.URLField(blank=True, verbose_name=_('Avatar / Logo URL'))
    html_override = models.TextField(blank=True, verbose_name=_('Custom HTML Override'))
    is_default = models.BooleanField(default=False, verbose_name=_('Default Signature'))

    class Meta:
        verbose_name = _('Email Signature')
        verbose_name_plural = _('Email Signatures')

    def __str__(self):
        return f"{self.name} ({self.email})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            EmailSignature.objects.exclude(pk=self.pk).filter(is_default=True).update(is_default=False)

    def render_html(self) -> str:
        if self.html_override.strip():
            return self.html_override

        avatar_html = (
            f'<td width="72" valign="top" style="padding-right:14px;">'
            f'<img src="{self.avatar_url}" alt="{self.sender_name}" width="64" height="64" '
            f'style="display:block;border-radius:50%;object-fit:cover;border:0;"></td>'
            if self.avatar_url else ""
        )
        title_html = (
            f'<div style="color:#0066cc;font-weight:600;margin-bottom:6px;">{self.sender_title}</div>'
            if self.sender_title else ""
        )
        contact_lines = []
        if self.website_url:
            contact_lines.append(
                f'<strong>W:</strong> <a href="{self.website_url}" style="color:#555555;">{self.website_url}</a>'
            )
        contact_lines.append(
            f'<strong>E:</strong> <a href="mailto:{self.email}" style="color:#555555;">{self.email}</a>'
        )
        if self.phone:
            contact_lines.append(
                f'<strong>P:</strong> <a href="tel:{self.phone}" style="color:#555555;">{self.phone}</a>'
            )

        return (
            f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" '
            f'style="border-top:1px solid #eeeeee;padding-top:18px;margin-top:20px;"><tr>{avatar_html}'
            f'<td valign="top" style="font-size:14px;line-height:1.45;color:#555555;">'
            f'<div style="font-size:16px;font-weight:bold;color:#111111;">{self.sender_name}</div>'
            f'{title_html}'
            f'<div style="font-size:13px;">{"<br>".join(contact_lines)}</div>'
            f'</td></tr></table>'
        )

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
    
class InquiryEmailTemplate(models.Model):
    SUBJECT_CATEGORY_CHOICES = [('all', _('All Subjects (Fallback)'))] + list(Inquiry.SUBJECT_CHOICES)

    name = models.CharField(max_length=120, verbose_name=_('Template Name'))
    subject_category = models.CharField(
        max_length=30,
        choices=SUBJECT_CATEGORY_CHOICES,
        default='all',
        verbose_name=_('Subject Category'),
    )
    # ... rest of fields stay the same ...
    name = models.CharField(max_length=120, verbose_name=_('Template Name'))
    subject_category = models.CharField(
        max_length=30,
        choices=list(
            # Uses Inquiry.SUBJECT_CHOICES plus a general fallback
            [("all", _("All Subjects (Fallback)"))]
        ),
        default="all",
        verbose_name=_('Subject Category'),
    )
    email_subject = models.CharField(
        max_length=200,
        verbose_name=_('Email Subject'),
        help_text=_('Supports variables like {{ inquiry.name }}, {{ inquiry.get_subject_display }}'),
    )
    body_html = models.TextField(
        verbose_name=_('Body HTML'),
        help_text=_('Supports {{ inquiry.name }}, {{ inquiry.email }}, {{ inquiry.message }}, {{ inquiry.admin_reply }}, {{ inquiry.get_subject_display }}'),
    )
    signature = models.ForeignKey(
        EmailSignature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='templates',
        verbose_name=_('Signature'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))

    class Meta:
        verbose_name = _('Inquiry Email Template')
        verbose_name_plural = _('Inquiry Email Templates')

    def __str__(self):
        return f"{self.name} [{self.get_subject_category_display()}]"

    def render_full_html(self, context_dict: dict) -> tuple[str, str]:
        ctx = Context(context_dict)
        rendered_subject = Template(self.email_subject).render(ctx).strip()
        rendered_body = Template(self.body_html).render(ctx)

        sig = self.signature or EmailSignature.objects.filter(is_default=True).first()
        sig_html = sig.render_html() if sig else ""

        full_html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:24px;background:#f4f5f7;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0"
         style="max-width:600px;width:100%;margin:0 auto;background:#ffffff;border-radius:8px;padding:32px;">
    <tr>
      <td style="color:#333333;font-size:16px;line-height:1.6;">
        {rendered_body}
        {sig_html}
      </td>
    </tr>
  </table>
</body>
</html>"""
        return rendered_subject, full_html


