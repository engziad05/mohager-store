"""
معالجات إرسال البريد الإلكتروني للطلبات والعمليات الأخرى
"""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order, OrderItem


@receiver(post_save, sender=Order)
def send_order_confirmation_email(sender, instance, created, **kwargs):
    """
    إرسال بريد تأكيد الطلب للعميل والمتجر عند إنشاء طلب جديد
    """
    if not created:  # فقط عند إنشاء طلب جديد
        return
    
    order = instance
    
    # الحصول على عناصر الطلب
    cart_items = OrderItem.objects.filter(order=order)
    
    # 1. إيميل للعميل
    if order.email:
        try:
            html_content = render_to_string('store/emails/order_confirm.html', {
                'order': order,
                'cart_items': cart_items,
                'base_url': "https://mohager-store-production.up.railway.app",
            })
            
            msg = EmailMultiAlternatives(
                subject=f"✓ تأكيد طلبك من مُهاجر - رقم #{order.tracking_no}",
                body="يرجى تفعيل HTML لعرض محتوى الرسالة.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
            
            print(f"✅ تم إرسال تأكيد الطلب للعميل: {order.email} - طلب #{order.tracking_no}")
        except Exception as e:
            print(f"❌ خطأ في إرسال بريد تأكيد الطلب: {str(e)}")
    
    # 2. إيميل إشعار لصاحب المتجر
    owner_email = getattr(settings, 'STORE_OWNER_EMAIL', None)
    if owner_email:
        try:
            # حساب إجمالي الطلب بالفعل موجود في order.total_price
            admin_html = render_to_string('store/emails/admin_order_notify.html', {
                'order': order,
                'cart_items': cart_items,
                'total_price': sum(item.price * item.quantity for item in cart_items),
                'grand_total': order.total_price,
            })
            
            admin_msg = EmailMultiAlternatives(
                subject=f"🔔 طلب جديد #{order.tracking_no} - {order.full_name}",
                body=f"طلب جديد من {order.full_name} - الهاتف: {order.phone}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[owner_email],
            )
            admin_msg.attach_alternative(admin_html, "text/html")
            admin_msg.send(fail_silently=False)
            
            print(f"✅ تم إرسال إشعار الطلب لصاحب المتجر: {owner_email} - طلب #{order.tracking_no}")
        except Exception as e:
            print(f"❌ خطأ في إرسال بريد الإشعار: {str(e)}")
