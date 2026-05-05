from django.dispatch import receiver
from allauth.account.signals import user_logged_in
from .models import Cart, CartItem

# الإشارة دي بتشتغل أوتوماتيك أول ما allauth ينجح في تسجيل دخول العميل
@receiver(user_logged_in)
def merge_carts_on_login(request, user, **kwargs):
    # 1. بنشوف هل الزائر ده كان عنده سلة في المتصفح (Session) قبل ما يسجل دخول؟
    session_cart_id = request.session.get('cart_id')
    
    if session_cart_id:
        try:
            # بنجيب سلة الزائر (اللي ملهاش يوزر)
            guest_cart = Cart.objects.get(id=session_cart_id, user__isnull=True)
            
            # 2. بنجيب سلة العميل اللي لسه مسجل دخول (أو بنعمله واحدة جديدة لو معندوش)
            user_cart, created = Cart.objects.get_or_create(user=user)
            
            # 3. بننقل المنتجات من سلة الزائر لسلة العميل
            for item in guest_cart.items.all():
                # لو المنتج موجود أصلاً في سلة العميل من قبل كده، بنزود الكمية بس
                user_item, item_created = CartItem.objects.get_or_create(
                    cart=user_cart,
                    product=item.product,
                    variant=item.variant,
                    defaults={'quantity': item.quantity}
                )
                if not item_created:
                    user_item.quantity += item.quantity
                    user_item.save()
            
            # 4. بنمسح سلة الزائر عشان ننضف الداتابيز
            guest_cart.delete()
            
            # 5. بنعرف المتصفح إن السلة الجديدة هي سلة العميل
            request.session['cart_id'] = user_cart.id
            
        except Cart.DoesNotExist:
            pass
