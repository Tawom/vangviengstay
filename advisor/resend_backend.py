import resend
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings


class ResendBackend(BaseEmailBackend):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        resend.api_key = settings.EMAIL_HOST_PASSWORD

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        num_sent = 0
        for message in email_messages:
            try:
                params = {
                    "from": message.from_email,
                    "to": message.to,
                    "subject": message.subject,
                    "html": message.body if message.content_subtype == 'html' else f"<p>{message.body}</p>",
                }
                resend.Emails.send(params)
                num_sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return num_sent