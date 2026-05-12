"""
Context Processor للسلة — بيحسب cart_count أوتوماتيك لكل الصفحات
بدل ما نكرر نفس الكود في كل view
"""
from .models import Cart, CartItem


def cart_context(request):
    """يرجع بيانات السلة (العدد، العناصر، الإجمالي) لكل صفحة أوتوماتيك."""
    cart_id = request.session.get('cart_id')

    if not cart_id:
        return {
            'cart_count': 0,
            'cart_items': [],
            'cart_total_price': 0,
        }

    cart = Cart.objects.filter(id=cart_id).first()
    if not cart:
        return {
            'cart_count': 0,
            'cart_items': [],
            'cart_total_price': 0,
        }

    items = CartItem.objects.filter(cart=cart).select_related('product', 'variant')
    cart_count = sum(item.quantity for item in items)
    cart_total = sum(item.total_price for item in items)

    return {
        'cart_count': cart_count,
        'cart_items': items,
        'cart_total_price': cart_total,
    }
