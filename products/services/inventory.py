"""Stock checks and mutations for catalog variants (used by cart and checkout)."""

import logging
from typing import Iterable

from django.conf import settings

from products.models import MasterStockVariant

logger = logging.getLogger(__name__)

LOW_STOCK_THRESHOLD = 5


def assert_sufficient_variant_stock(variant: MasterStockVariant, quantity: int) -> None:
    if quantity < 1:
        raise ValueError('Quantity must be at least 1.')
    if not variant:
        raise ValueError('Variant is required for stock check.')
    if variant.stock < quantity:
        raise ValueError('Insufficient stock.')


def consume_stock_for_cart_items(cart_items: Iterable) -> None:
    """
    Decrement stock for each line (expects items with .variant, .quantity, .product for messages).
    Uses select_for_update on each variant row.
    Sends a low-stock email alert when stock drops to threshold or below.
    """
    low_stock_alerts = []

    for item in cart_items:
        if not item.variant_id:
            continue
        variant = MasterStockVariant.objects.select_for_update().get(pk=item.variant_id)
        if variant.stock < item.quantity:
            raise ValueError(
                f'عفواً، الكمية المتاحة من {item.product.name_ar} مقاس {variant.size} لم تعد تكفي.'
            )
        variant.stock -= item.quantity
        variant.save(update_fields=['stock'])

        # Check if stock dropped to or below threshold
        if variant.stock <= LOW_STOCK_THRESHOLD:
            low_stock_alerts.append({
                'product_name': item.product.name_ar,
                'product_name_en': item.product.name_en,
                'size': variant.size or '-',
                'remaining': variant.stock,
            })

    # Fire low-stock email alerts (non-blocking via Celery)
    if low_stock_alerts:
        _send_low_stock_alert(low_stock_alerts)


def _send_low_stock_alert(alerts: list) -> None:
    """Send a low-stock warning email to the store owner via Celery."""
    from notifications.tasks import send_email_task

    owner_email = getattr(settings, 'STORE_OWNER_EMAIL', None)
    if not owner_email:
        logger.info("Skipping low-stock alert because STORE_OWNER_EMAIL is empty")
        return

    # Build a simple HTML table for the alert
    rows = ''
    for item in alerts:
        emoji = '🔴' if item['remaining'] == 0 else '🟡'
        rows += (
            f'<tr>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #333;">{emoji} {item["product_name"]}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #333;text-align:center;">{item["size"]}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #333;text-align:center;font-weight:bold;'
            f'color:{"#ff4444" if item["remaining"] == 0 else "#ffaa00"};">{item["remaining"]}</td>'
            f'</tr>'
        )

    html_message = f'''
    <div style="direction:rtl;font-family:Arial,sans-serif;background:#0a0a0a;color:#fff;padding:30px;border-radius:12px;max-width:500px;">
        <h2 style="color:#d4af37;margin-bottom:5px;">⚠️ تنبيه مخزون منخفض</h2>
        <p style="color:#999;font-size:14px;">المنتجات التالية وصل مخزونها لأقل من {LOW_STOCK_THRESHOLD} قطع:</p>
        <table style="width:100%;border-collapse:collapse;margin-top:15px;">
            <thead>
                <tr style="background:rgba(212,175,55,0.1);">
                    <th style="padding:10px 12px;text-align:right;color:#d4af37;border-bottom:2px solid #d4af37;">المنتج</th>
                    <th style="padding:10px 12px;text-align:center;color:#d4af37;border-bottom:2px solid #d4af37;">المقاس</th>
                    <th style="padding:10px 12px;text-align:center;color:#d4af37;border-bottom:2px solid #d4af37;">المتبقي</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        <p style="color:#666;font-size:12px;margin-top:20px;">🔴 = نفذ تماماً &nbsp; 🟡 = مخزون منخفض</p>
    </div>
    '''

    count = len(alerts)
    subject = f'⚠️ تنبيه مخزون - {count} منتج{"ات" if count > 1 else ""} وصل لأقل من {LOW_STOCK_THRESHOLD} قطع'

    send_email_task.delay(
        subject=subject,
        body=f'{count} products have reached low stock levels.',
        recipient_list=[owner_email],
        html_message=html_message,
    )
    logger.info("Queued low-stock alert for %d items to %s", count, owner_email)


def restore_stock_for_order_items(order) -> None:
    """Restore variant stock when an order is cancelled (mirrors OrderService.cancel_order)."""
    for line in order.items.all():
        if line.variant_id:
            variant = MasterStockVariant.objects.select_for_update().get(pk=line.variant_id)
            variant.stock += line.quantity
            variant.save(update_fields=['stock'])
