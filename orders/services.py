from django.db import transaction
from django.core.cache import cache
from store.models import Order, OrderItem, ProductVariant, Cart, CartItem
from notifications.tasks import send_order_confirmation_email, send_cancellation_email


class OrderService:
    """Service layer for order-related business logic."""
    
    @staticmethod
    @transaction.atomic
    def create_order(user, cart, shipping_data):
        """
        Create an order from cart items.
        
        Args:
            user: The user placing the order
            cart: The cart object
            shipping_data: Dictionary containing shipping information
            
        Returns:
            Order object
        """
        # Validate cart
        if not cart.items.exists():
            raise ValueError("Cart is empty")
        
        # Validate stock
        for cart_item in cart.items.all():
            if cart_item.variant and cart_item.quantity > cart_item.variant.stock:
                raise ValueError(f"Insufficient stock for {cart_item.product.name_en}")
        
        # Create order
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
            status='Pending'
        )
        
        # Create order items and update stock
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                price=cart_item.product.base_price
            )
            
            # Update stock
            if cart_item.variant:
                cart_item.variant.stock -= cart_item.quantity
                cart_item.variant.save()
        
        # Clear cart
        cart.items.all().delete()
        
        # Invalidate cache
        cache.delete(f'user_cart_{user.id}')
        
        # Send confirmation email asynchronously
        send_order_confirmation_email.delay(order.id)
        
        return order
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order_id, user):
        """
        Cancel an order and restore stock.
        
        Args:
            order_id: The order ID
            user: The user requesting cancellation
            
        Returns:
            Order object
        """
        order = Order.objects.get(id=order_id)
        
        # Check permissions
        if order.user != user and not user.is_staff:
            raise PermissionError("You don't have permission to cancel this order")
        
        # Check if order can be cancelled
        if order.status not in ['Pending', 'Processing']:
            raise ValueError("This order cannot be cancelled")
        
        # Restore stock
        for item in order.items.all():
            if item.variant:
                item.variant.stock += item.quantity
                item.variant.save()
        
        # Update order status
        order.status = 'Cancelled'
        order.save()
        
        # Send cancellation email asynchronously
        send_cancellation_email.delay(order.id)
        
        return order
    
    @staticmethod
    def get_user_orders(user, limit=20):
        """
        Get user's orders with caching.
        
        Args:
            user: The user
            limit: Maximum number of orders to return
            
        Returns:
            QuerySet of orders
        """
        cache_key = f'user_orders_{user.id}'
        orders = cache.get(cache_key)
        
        if orders is None:
            orders = Order.objects.filter(user=user).order_by('-created_at')[:limit]
            cache.set(cache_key, orders, 300)  # Cache for 5 minutes
        
        return orders
