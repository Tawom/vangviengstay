from django.conf import settings
from django.contrib import admin, messages
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html, strip_tags

from .models import Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'email',
        'subject',
        'status_badge',
        'customer_email_sent',
        'admin_email_sent',
        'created_at',
        'reply_button',
    )
    list_filter = ('status', 'subject', 'created_at')
    search_fields = ('name', 'email', 'message', 'phone', 'admin_reply')
    readonly_fields = (
        'created_at',
        'updated_at',
        'customer_email_sent',
        'admin_email_sent',
        'replied_at',
        'replied_by',
        'reply_button',
    )

    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'subject')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Admin Response', {
            'fields': ('reply_button', 'admin_reply', 'replied_at', 'replied_by')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'customer_email_sent', 'admin_email_sent', 'created_at', 'updated_at')
        }),
    )

    actions = ['mark_as_read', 'mark_as_responded', 'mark_as_closed']

    def change_view(self, request, object_id, form_url='', extra_context=None):
        Inquiry.objects.filter(pk=object_id, status='new').update(status='read')
        return super().change_view(request, object_id, form_url, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:inquiry_id>/reply/',
                self.admin_site.admin_view(self.reply_view),
                name='inquiry_inquiry_reply',
            ),
        ]
        return custom_urls + urls

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        styles = {
            'new': ('#dbeafe', '#1e40af'),
            'read': ('#fef3c7', '#92400e'),
            'responded': ('#dcfce7', '#166534'),
            'closed': ('#f1f5f9', '#475569'),
        }
        bg, fg = styles.get(obj.status, ('#f1f5f9', '#334155'))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:999px;font-weight:600;font-size:12px;">{}</span>',
            bg,
            fg,
            obj.get_status_display(),
        )

    @admin.display(description='Action')
    def reply_button(self, obj):
        if not obj.pk:
            return '-'
        url = reverse('admin:inquiry_inquiry_reply', args=[obj.pk])
        label = 'Send Another Reply' if obj.status == 'responded' else 'Reply via Email'
        return format_html(
            '<a class="button" href="{}" style="background:#483D8B;color:#fff;padding:6px 12px;border-radius:6px;text-decoration:none;font-weight:600;white-space:nowrap;">{}</a>',
            url,
            label,
        )

    def mark_as_read(self, request, queryset):
        queryset.update(status='read')
    mark_as_read.short_description = "Mark selected as Read"

    def mark_as_responded(self, request, queryset):
        queryset.update(status='responded')
    mark_as_responded.short_description = "Mark selected as Responded"

    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')
    mark_as_closed.short_description = "Mark selected as Closed"

    def reply_view(self, request, inquiry_id):
        inquiry = get_object_or_404(Inquiry, pk=inquiry_id)

        if request.method == 'POST':
            reply_subject = request.POST.get('reply_subject', '').strip()
            reply_message = request.POST.get('reply_message', '').strip()

            if not reply_subject or not reply_message:
                messages.error(request, 'Both subject and reply message are required.')
            else:
                html_content = render_to_string(
                    'emails/inquiry_reply.html',
                    {
                        'inquiry': inquiry,
                        'reply_message': reply_message,
                    },
                )
                text_content = strip_tags(html_content)

                email = EmailMultiAlternatives(
                    subject=reply_subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[inquiry.email],
                    reply_to=['info@vangviengstay.com'],
                )
                email.attach_alternative(html_content, 'text/html')

                try:
                    email.send(fail_silently=False)
                    inquiry.status = 'responded'
                    inquiry.admin_reply = reply_message
                    inquiry.replied_at = timezone.now()
                    inquiry.replied_by = request.user
                    inquiry.save(update_fields=['status', 'admin_reply', 'replied_at', 'replied_by', 'updated_at'])

                    messages.success(request, f'Reply sent to {inquiry.email} and status updated to Responded.')
                    return redirect('admin:inquiry_inquiry_changelist')
                except Exception as exc:
                    messages.error(request, f'Failed to send email: {exc}')

        context = {
            **self.admin_site.each_context(request),
            'title': f'Reply to {inquiry.name}',
            'inquiry': inquiry,
            'opts': self.model._meta,
        }
        return render(request, 'admin/inquiry/reply_form.html', context)