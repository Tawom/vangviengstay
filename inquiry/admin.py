from django.conf import settings
from django.contrib import admin, messages
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404, redirect, render
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html, strip_tags

from .models import EmailSignature, Inquiry, InquiryEmailTemplate


def _get_default_template_for_inquiry(inquiry: Inquiry) -> InquiryEmailTemplate | None:
    return (
        InquiryEmailTemplate.objects.filter(subject_category=inquiry.subject, is_active=True)
        .select_related('signature')
        .first()
        or InquiryEmailTemplate.objects.filter(subject_category='all', is_active=True)
        .select_related('signature')
        .first()
    )


def _get_signature(selected_sig_id: str | None, template: InquiryEmailTemplate | None) -> EmailSignature | None:
    if selected_sig_id:
        sig = EmailSignature.objects.filter(pk=selected_sig_id).first()
        if sig:
            return sig
    if template and template.signature:
        return template.signature
    return EmailSignature.objects.filter(is_default=True).first()


@admin.register(EmailSignature)
class EmailSignatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'sender_name', 'sender_title', 'email', 'is_default')
    list_editable = ('is_default',)
    search_fields = ('name', 'sender_name', 'email')


@admin.register(InquiryEmailTemplate)
class InquiryEmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject_category', 'email_subject', 'signature', 'is_active')
    list_filter = ('subject_category', 'is_active')
    search_fields = ('name', 'email_subject', 'body_html')


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
        templates = InquiryEmailTemplate.objects.filter(is_active=True).select_related('signature')
        signatures = EmailSignature.objects.all()
        matched_template = _get_default_template_for_inquiry(inquiry)

        selected_template_id = request.POST.get('template_id') or request.GET.get('template_id')
        selected_signature_id = request.POST.get('signature_id') or request.GET.get('signature_id')

        active_template = (
            templates.filter(pk=selected_template_id).first()
            if selected_template_id
            else matched_template
        )
        active_signature = _get_signature(selected_signature_id, active_template)

        render_ctx = {
            'inquiry': inquiry,
            'user': request.user,
            'signature_html': active_signature.render_html() if active_signature else '',
        }

        default_subject = (
            Template(active_template.email_subject).render(Context(render_ctx)).strip()
            if active_template
            else f'Re: {inquiry.get_subject_display()}'
        )
        default_message = (
            Template(active_template.body_html).render(Context(render_ctx)).strip()
            if active_template
            else ''
        )

        if request.method == 'POST' and request.POST.get('action') != 'load_template':
            reply_subject = request.POST.get('reply_subject', '').strip()
            reply_message = request.POST.get('reply_message', '').strip()
            reply_to_addr = (
                active_signature.email
                if active_signature and active_signature.email
                else 'info@vangviengstay.com'
            )

            if not reply_subject or not reply_message:
                messages.error(request, 'Both subject and reply message are required.')
            else:
                ctx_with_reply = {
                    **render_ctx,
                    'reply_message': reply_message,
                }
                if active_template:
                    _, html_content = active_template.render_full_html(ctx_with_reply)
                else:
                    html_content = render_to_string('emails/inquiry_reply.html', ctx_with_reply)

                text_content = strip_tags(html_content)

                email = EmailMultiAlternatives(
                    subject=reply_subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[inquiry.email],
                    reply_to=[reply_to_addr],
                )
                email.attach_alternative(html_content, 'text/html')

                try:
                    email.send(fail_silently=False)
                    inquiry.status = 'responded'
                    inquiry.customer_email_sent = True
                    inquiry.admin_reply = strip_tags(reply_message)
                    inquiry.replied_at = timezone.now()
                    inquiry.replied_by = request.user
                    inquiry.save(
                        update_fields=[
                            'status',
                            'customer_email_sent',
                            'admin_reply',
                            'replied_at',
                            'replied_by',
                            'updated_at',
                        ]
                    )

                    messages.success(request, f'Reply sent to {inquiry.email} and status updated to Responded.')
                    return redirect('admin:inquiry_inquiry_changelist')
                except Exception as exc:
                    messages.error(request, f'Failed to send email: {exc}')

        context = {
            **self.admin_site.each_context(request),
            'title': f'Reply to {inquiry.name}',
            'inquiry': inquiry,
            'opts': self.model._meta,
            'templates': templates,
            'signatures': signatures,
            'active_template': active_template,
            'active_signature': active_signature,
            'default_subject': default_subject,
            'default_message': default_message,
        }
        return render(request, 'admin/inquiry/reply_form.html', context)