import os
import resend
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class ResendBackend(BaseEmailBackend):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        api_key = (
            getattr(settings, "RESEND_API_KEY", "")
            or getattr(settings, "EMAIL_HOST_PASSWORD", "")
            or os.getenv("RESEND_API_KEY", "")
        )
        resend.api_key = api_key

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        if not resend.api_key:
            api_key = (
                getattr(settings, "RESEND_API_KEY", "")
                or getattr(settings, "EMAIL_HOST_PASSWORD", "")
                or os.getenv("RESEND_API_KEY", "")
            )
            resend.api_key = api_key

        num_sent = 0
        for message in email_messages:
            try:
                html_content = None
                text_content = None

                # Extract HTML alternative from EmailMultiAlternatives if present
                alternatives = getattr(message, "alternatives", [])
                for content, mimetype in alternatives:
                    if mimetype == "text/html":
                        html_content = content
                        break

                if message.content_subtype == "html":
                    html_content = message.body
                elif not html_content:
                    text_content = message.body

                params = {
                    "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
                    "to": list(message.to),
                    "subject": message.subject,
                }
                if html_content:
                    params["html"] = html_content
                if text_content:
                    params["text"] = text_content
                if message.cc:
                    params["cc"] = list(message.cc)
                if message.bcc:
                    params["bcc"] = list(message.bcc)
                if message.reply_to:
                    params["reply_to"] = (
                        message.reply_to[0]
                        if len(message.reply_to) == 1
                        else list(message.reply_to)
                    )

                resend.Emails.send(params)
                num_sent += 1
            except Exception:
                if not self.fail_silently:
                    raise

        return num_sent