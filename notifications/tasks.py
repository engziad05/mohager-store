from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from store.models import Order


@shared_task
def send_order_confirmation_email(order_id):
    """
    Send order confirmation email to customer.
    """
    try:
        order = Order.objects.get(id=order_id)
        
        subject = f'تم استلام طلبك #{order.tracking_no} - مُهاجر ستور'
        
        context = {
            'order': order,
            'order_items': order.items.all(),
            'total_price': order.total_price,
        }
        
        html_message = render_to_string('emails/order_confirmation.html', context)
        
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return f"Email sent for order {order_id}"
    except Exception as e:
        return f"Failed to send email for order {order_id}: {str(e)}"


@shared_task
def send_cancellation_email(order_id):
    """
    Send order cancellation email to customer.
    """
    try:
        order = Order.objects.get(id=order_id)
        
        subject = f'تم إلغاء طلبك #{order.tracking_no} - مُهاجر ستور'
        
        context = {
            'order': order,
            'tracking_no': order.tracking_no,
        }
        
        html_message = render_to_string('emails/order_cancellation.html', context)
        
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return f"Cancellation email sent for order {order_id}"
    except Exception as e:
        return f"Failed to send cancellation email for order {order_id}: {str(e)}"


@shared_task
def send_shipping_notification_email(order_id):
    """
    Send shipping notification email to customer.
    """
    try:
        order = Order.objects.get(id=order_id)
        
        subject = f'تم شحن طلبك #{order.tracking_no} - مُهاجر ستور'
        
        context = {
            'order': order,
            'tracking_no': order.tracking_no,
        }
        
        html_message = render_to_string('emails/shipping_notification.html', context)
        
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return f"Shipping notification sent for order {order_id}"
    except Exception as e:
        return f"Failed to send shipping notification for order {order_id}: {str(e)}"
