import logging

from allauth.account.adapter import DefaultAccountAdapter

from .tasks import send_email_task

logger = logging.getLogger(__name__)


class AsyncAccountAdapter(DefaultAccountAdapter):
    """Queue django-allauth emails for background delivery."""

    def send_mail(self, template_prefix, email, context):
        message = self.render_mail(template_prefix, email, context)
        alternatives = [
            {'content': content, 'mimetype': mimetype}
            for content, mimetype in getattr(message, 'alternatives', [])
        ]

        try:
            send_email_task.delay(
                subject=message.subject,
                body=message.body,
                recipient_list=message.to,
                from_email=message.from_email,
                html_message=None,
                alternatives=alternatives,
                headers=message.extra_headers,
                reply_to=message.reply_to,
            )
        except Exception:
            logger.exception("Failed to enqueue allauth email to %s", email)
            raise
