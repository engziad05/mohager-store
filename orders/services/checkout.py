"""Order creation, cancellation, and storefront checkout orchestration."""

from __future__ import annotations

from typing import Any, Mapping

from django.core.cache import cache
from django.db import transaction

from cart.models import Cart
from orders.models import Order, OrderItem
from products.services.inventory import (
    consume_stock_for_cart_items,
    restore_stock_for_order_items,
)
from notifications.tasks import send_cancellation_email


class OrderService:
    """API-oriented checkout from an authenticated user's cart."""

    @staticmethod
    @transaction.atomic
    def create_order(user, cart: Cart, shipping_data: Mapping[str, Any]) -> Order:
        if not cart.items.exists():
            raise ValueError('Cart is empty')

        consume_stock_for_cart_items(cart.items.all())

        order = Order.objects.create(
            user=user,
            full_name=shipping_data.get('full_name'),
            phone=shipping_data.get('phone'),
            email=shipping_data.get('email', user.email),
            region=shipping_data.get('region'),
            address=shipping_data.get('address'),
            building=shipping_data.get('building', '-'),
            floor=shipping_data.get('floor', '-'),
            apartment=shipping_data.get('apartment', '-'),
            landmark=shipping_data.get('landmark', ''),
            total_price=cart.total_price,
            status='Pending',
        )

        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                product_print=cart_item.product_print,
                quantity=cart_item.quantity,
                price=cart_item.product.base_price,
            )

        if shipping_data.get('phone') and hasattr(user, 'phone'):
            user.phone = shipping_data.get('phone')
            user.save(update_fields=['phone'])

        cart.items.all().delete()
        cache.delete(f'user_cart_{user.id}')
        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(order_id: int, user) -> Order:
        order = Order.objects.get(id=order_id)
        if order.user != user and not user.is_staff:
            raise PermissionError("You don't have permission to cancel this order")
        if order.status not in ['Pending', 'Processing']:
            raise ValueError('This order cannot be cancelled')

        restore_stock_for_order_items(order)
        order.status = 'Cancelled'
        order.save(update_fields=['status'])
        send_cancellation_email.delay(order.id)
        return order

    @staticmethod
    def get_user_orders(user, limit: int = 20):
        cache_key = f'user_orders_{user.id}'
        orders = cache.get(cache_key)
        if orders is None:
            orders = list(Order.objects.filter(user=user).order_by('-created_at')[:limit])
            cache.set(cache_key, orders, 300)
        return orders


@transaction.atomic
def complete_storefront_checkout(
    *,
    cart: Cart,
    cart_items,
    user,
    post_data: Mapping[str, Any],
    grand_total,
):
    """
    Session-based checkout used by the legacy storefront view.
    Persists SavedAddress for authenticated users; deletes the session cart.
    """
    from store.models import SavedAddress

    lines = list(cart_items)
    consume_stock_for_cart_items(lines)

    order = Order.objects.create(
        user=user if user and user.is_authenticated else None,
        full_name=post_data.get('full_name'),
        phone=post_data.get('phone'),
        email=post_data.get('email'),
        address=post_data.get('address'),
        building=post_data.get('building'),
        floor=post_data.get('floor'),
        apartment=post_data.get('apartment'),
        landmark=post_data.get('landmark'),
        region=post_data.get('region'),
        total_price=grand_total,
        status='Pending',
    )

    if user and user.is_authenticated:
        address_record, _ = SavedAddress.objects.get_or_create(user=user)
        address_record.phone = post_data.get('phone')
        address_record.region = post_data.get('region')
        address_record.address = post_data.get('address')
        address_record.building = post_data.get('building')
        address_record.floor = post_data.get('floor')
        address_record.apartment = post_data.get('apartment')
        address_record.landmark = post_data.get('landmark')
        address_record.save()

        if post_data.get('phone') and hasattr(user, 'phone'):
            user.phone = post_data.get('phone')
            user.save(update_fields=['phone'])

    for item in lines:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            variant=item.variant,
            product_print=item.product_print,
            quantity=item.quantity,
            price=item.product.base_price,
        )

    cart.delete()
    return order
