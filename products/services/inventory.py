"""Stock checks and mutations for catalog variants (used by cart and checkout)."""

from typing import Iterable

from products.models import ProductVariant


def assert_sufficient_variant_stock(variant: ProductVariant, quantity: int) -> None:
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
    """
    for item in cart_items:
        if not item.variant_id:
            continue
        variant = ProductVariant.objects.select_for_update().get(pk=item.variant_id)
        if variant.stock < item.quantity:
            raise ValueError(
                f'عفواً، الكمية المتاحة من {item.product.name_ar} مقاس {variant.size} لم تعد تكفي.'
            )
        variant.stock -= item.quantity
        variant.save(update_fields=['stock'])


def restore_stock_for_order_items(order) -> None:
    """Restore variant stock when an order is cancelled (mirrors OrderService.cancel_order)."""
    for line in order.items.all():
        if line.variant_id:
            variant = ProductVariant.objects.select_for_update().get(pk=line.variant_id)
            variant.stock += line.quantity
            variant.save(update_fields=['stock'])
