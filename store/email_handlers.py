"""Order email signal handlers."""

import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.tasks import send_new_order_emails
from orders.models import Order

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def queue_order_confirmation_emails(sender, instance, created, **kwargs):
    """Queue customer and owner emails after a new order commits."""
    if not created:
        return

    order_id = instance.id

    def enqueue_order_emails():
        import threading
        # Run the celery task synchronously inside a background thread
        thread = threading.Thread(target=send_new_order_emails, args=(order_id,))
        thread.start()
        logger.info("Started background thread for order emails: %s", order_id)

    transaction.on_commit(enqueue_order_emails)
