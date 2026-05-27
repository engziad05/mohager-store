import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

from orders.models import Order

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def send_email_task(
    self,
    *,
    subject,
    body,
    recipient_list,
    from_email=None,
    html_message=None,
    alternatives=None,
    headers=None,
    reply_to=None,
):
    """Send a generic email payload in the background."""
    if not recipient_list:
        logger.info("Skipping email with no recipients: %s", subject)
        return "skipped"

    message = EmailMultiAlternatives(
        subject=subject,
        body=body or '',
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        to=recipient_list,
        headers=headers or None,
        reply_to=reply_to or None,
    )

    if html_message:
        message.attach_alternative(html_message, "text/html")

    for alternative in alternatives or []:
        message.attach_alternative(
            alternative['content'],
            alternative.get('mimetype', 'text/html'),
        )

    sent_count = message.send(fail_silently=False)
    logger.info("Sent email '%s' to %s", subject, recipient_list)
    return sent_count


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def send_order_confirmation_email(self, order_id):
    """Send an order confirmation email to the customer."""
    order = Order.objects.prefetch_related('items__product', 'items__variant').get(id=order_id)
    if not order.email:
        logger.info("Skipping customer order email for order %s with no email", order_id)
        return "skipped"

    html_message = render_to_string('store/emails/order_confirm.html', {
        'order': order,
        'cart_items': order.items.all(),
        'base_url': getattr(settings, 'SITE_URL', 'https://mohager-store-production.up.railway.app'),
    })

    return send_email_task(
        subject=f"Order confirmation #{order.tracking_no}",
        body="Your order has been received. Please enable HTML to view the full message.",
        recipient_list=[order.email],
        html_message=html_message,
    )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def send_order_owner_notification_email(self, order_id):
    """Notify the store owner about a new order."""
    owner_email = getattr(settings, 'STORE_OWNER_EMAIL', None)
    if not owner_email:
        logger.info("Skipping owner order email for order %s because STORE_OWNER_EMAIL is empty", order_id)
        return "skipped"

    order = Order.objects.prefetch_related('items__product', 'items__variant').get(id=order_id)
    cart_items = order.items.all()
    html_message = render_to_string('store/emails/admin_order_notify.html', {
        'order': order,
        'cart_items': cart_items,
        'total_price': sum(item.price * item.quantity for item in cart_items),
        'grand_total': order.total_price,
        'admin_order_url': f'{settings.SITE_URL}{settings.MOHAGER_ADMIN_URL}orders/order/{order.id}/change/',
    })

    return send_email_task(
        subject=f"New order #{order.tracking_no} - {order.full_name}",
        body=f"New order from {order.full_name} - phone: {order.phone}",
        recipient_list=[owner_email],
        html_message=html_message,
    )


@shared_task
def send_new_order_emails(order_id):
    """Send all emails related to a newly created order synchronously."""
    try:
        send_order_confirmation_email(order_id)
        send_order_owner_notification_email(order_id)
        return "sent"
    except Exception as e:
        logger.error("Error sending order emails for order %s: %s", order_id, e)
        return "error"


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def send_cancellation_email(self, order_id):
    """Send order cancellation email to customer."""
    order = Order.objects.get(id=order_id)
    if not order.email:
        return "skipped"

    context = {'order': order, 'tracking_no': order.tracking_no}
    try:
        html_message = render_to_string('emails/order_cancellation.html', context)
    except TemplateDoesNotExist:
        html_message = None

    return send_email_task(
        subject=f"Order cancelled #{order.tracking_no}",
        body=f"Your order #{order.tracking_no} has been cancelled.",
        recipient_list=[order.email],
        html_message=html_message,
    )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def send_shipping_notification_email(self, order_id):
    """Send shipping notification email to customer."""
    order = Order.objects.get(id=order_id)
    if not order.email:
        return "skipped"

    context = {'order': order, 'tracking_no': order.tracking_no}
    try:
        html_message = render_to_string('emails/shipping_notification.html', context)
    except TemplateDoesNotExist:
        html_message = None

    return send_email_task(
        subject=f"Order shipped #{order.tracking_no}",
        body=f"Your order #{order.tracking_no} has been shipped.",
        recipient_list=[order.email],
        html_message=html_message,
    )
