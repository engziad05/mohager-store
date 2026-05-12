"""
Views الخاصة بالمتجر — مُهاجر
تم إعادة هيكلتها: إزالة الكود المكرر + logging احترافي
cart_count بقى أوتوماتيك عبر Context Processor
"""
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django_ratelimit.decorators import ratelimit

from .forms import SavedAddressForm
from .models import (
    Cart, CartItem, Category, HeroSlide,
    Order, OrderItem, Product, ProductImage,
    ProductVariant, SavedAddress, StoreSetting,
)

logger = logging.getLogger('store')


# ============================================================
# Helper — جلب سلة الزائر الحالية
# ============================================================
def _get_cart(request):
    """يرجع (cart, cart_items) أو (None, []) لو مفيش سلة."""
    cart_id = request.session.get('cart_id')
    if not cart_id:
        return None, CartItem.objects.none()
    cart = Cart.objects.filter(id=cart_id).first()
    if not cart:
        return None, CartItem.objects.none()
    items = CartItem.objects.filter(cart=cart).select_related('product', 'variant')
    return cart, items


# ============================================================
# الصفحة الرئيسية
# ============================================================
def index(request):
    products = Product.objects.filter(is_active=True).select_related('category')[:8]
    slides = HeroSlide.objects.filter(is_active=True).order_by('order')

    # cart_count بيتحسب أوتوماتيك من الـ Context Processor
    # بس محتاجين cart_items و total_price للـ drawer في الهوم بيدج
    cart, cart_items = _get_cart(request)
    total_price = sum(item.total_price for item in cart_items) if cart_items else 0

    context = {
        'products': products,
        'slides': slides,
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'store/index.html', context)


# ============================================================
# صفحة المتجر
# ============================================================
def shop(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    categories = Category.objects.filter(is_active=True)

    query = request.GET.get('q')
    category_slug = request.GET.get('category')

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if query:
        products = products.filter(
            Q(name_ar__icontains=query) |
            Q(name_en__icontains=query) |
            Q(description_ar__icontains=query)
        )

    # cart_count أوتوماتيك من الـ Context Processor ✅

    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'store/shop.html', context)


# ============================================================
# صفحة تفاصيل المنتج
# ============================================================
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variants = ProductVariant.objects.filter(product=product)
    extra_images = ProductImage.objects.filter(product=product)

    # cart_count أوتوماتيك من الـ Context Processor ✅

    context = {
        'product': product,
        'variants': variants,
        'extra_images': extra_images,
    }
    return render(request, 'store/product_detail.html', context)


# ============================================================
# صفحة السلة
# ============================================================
def cart_detail(request):
    cart, cart_items = _get_cart(request)
    total_price = sum(item.total_price for item in cart_items) if cart_items else 0
    shipping_cost = 0
    grand_total = 0

    if total_price > 0:
        setting = StoreSetting.objects.first()
        shipping_cost = setting.shipping_cost if setting else 0
        grand_total = total_price + shipping_cost

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)


# ============================================================
# حذف عنصر من السلة
# ============================================================
def remove_cart_item(request, item_id):
    cart_id = request.session.get('cart_id')
    cart_item = get_object_or_404(CartItem, id=item_id, cart_id=cart_id)
    cart_item.delete()
    logger.info(f"Cart item #{item_id} removed from cart #{cart_id}")
    messages.success(request, 'تم حذف القطعة من السلة 🗑️')
    return redirect('cart_detail')


# ============================================================
# تعديل الكمية
# ============================================================
def update_quantity(request, item_id, action):
    cart_id = request.session.get('cart_id')
    cart_item = get_object_or_404(CartItem, id=item_id, cart_id=cart_id)

    if action == 'increase':
        if cart_item.quantity + 1 > cart_item.variant.stock:
            messages.error(request, f'عفواً، لا يوجد سوى {cart_item.variant.stock} قطع متاحة في المخزون.')
        else:
            cart_item.quantity += 1
            cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            messages.success(request, 'تم حذف القطعة من السلة 🗑️')

    if request.headers.get('HX-Request'):
        cart = cart_item.cart
        cart_items = CartItem.objects.filter(cart=cart).select_related('product', 'variant')
        total_price = sum(item.total_price for item in cart_items)
        cart_count = sum(item.quantity for item in cart_items)

        context = {
            'cart': cart,
            'cart_items': cart_items,
            'total_price': total_price,
            'grand_total': total_price,
            'cart_count': cart_count,
        }
        return render(request, 'store/partials/cart_items.html', context)

    return redirect('cart_detail')


# ============================================================
# صفحة نجاح الطلب
# ============================================================
def order_success(request):
    tracking_no = request.session.get('last_order_tracking', 'MHG-000000')
    order_id = request.session.get('last_order_id', None)
    context = {
        'tracking_no': tracking_no,
        'order_id': order_id,
    }
    return render(request, 'store/order_success.html', context)


# ============================================================
# درج السلة (HTMX)
# ============================================================
def cart_drawer(request):
    cart, cart_items = _get_cart(request)
    total_price = sum(item.total_price for item in cart_items) if cart_items else 0
    cart_count = sum(item.quantity for item in cart_items) if cart_items else 0

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
        'grand_total': total_price,
        'cart_count': cart_count,
    }
    return render(request, 'store/partials/cart_items.html', context)


# ============================================================
# إضافة للسلة
# ============================================================
def add_to_cart(request, product_id):
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')

        if not variant_id:
            messages.error(request, 'من فضلك اختر المقاس أولاً!')
            return redirect('product_detail', product_id=product_id)

        product = get_object_or_404(Product, id=product_id)
        variant = get_object_or_404(ProductVariant, id=variant_id)

        if variant.stock <= 0:
            messages.error(request, 'عفواً، هذا المقاس نفد من المخزون حالياً!')
            return redirect('product_detail', product_id=product.id)

        cart_id = request.session.get('cart_id')
        if cart_id:
            cart = Cart.objects.filter(id=cart_id).first()
            if not cart:
                cart = Cart.objects.create()
                request.session['cart_id'] = cart.id
        else:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
        )

        if not created:
            if cart_item.quantity + 1 > variant.stock:
                messages.error(request, f'عفواً، أقصى كمية متاحة من هذا المقاس هي {variant.stock} قطع!')
                return redirect('product_detail', product_id=product.id)
            cart_item.quantity += 1
            cart_item.save()

        logger.info(f"Product #{product_id} (variant #{variant_id}) added to cart #{cart.id}")

        if request.headers.get('HX-Request'):
            cart_items = CartItem.objects.filter(cart=cart).select_related('product', 'variant')
            total_price = sum(item.total_price for item in cart_items)
            cart_count = sum(item.quantity for item in cart_items)

            context = {
                'cart': cart,
                'cart_items': cart_items,
                'total_price': total_price,
                'grand_total': total_price,
                'cart_count': cart_count,
            }
            return render(request, 'store/partials/cart_items.html', context)

        messages.success(request, 'تم إضافة القطعة للسلة بنجاح! 🛒')
        return redirect('product_detail', product_id=product.id)

    return redirect('index')


# ============================================================
# لوحة تحكم العميل (Dashboard)
# ============================================================
@login_required(login_url='/accounts/login/')
def dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    try:
        saved_address = request.user.saved_address
    except SavedAddress.DoesNotExist:
        saved_address = None

    if request.method == 'POST':
        form = SavedAddressForm(request.POST, instance=saved_address)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
    else:
        form = SavedAddressForm(instance=saved_address)

    context = {
        'orders': orders,
        'form': form,
    }
    return render(request, 'dashboard.html', context)


# ============================================================
# تفاصيل الطلب
# ============================================================
@login_required(login_url='/accounts/login/')
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {'order': order}
    return render(request, 'order_detail.html', context)


# ============================================================
# الدفع والتحقق (Checkout)
# ============================================================
@ratelimit(key='ip', rate='5/m', block=True)
def checkout(request):
    cart_id = request.session.get('cart_id')

    if not cart_id:
        return redirect('index')

    cart = Cart.objects.filter(id=cart_id).first()
    if not cart:
        return redirect('index')

    cart_items = CartItem.objects.filter(cart=cart).select_related('product', 'variant')
    if not cart_items.exists():
        return redirect('index')

    total_price = sum(item.total_price for item in cart_items)
    setting = StoreSetting.objects.first()
    shipping_cost = setting.shipping_cost if setting else 0
    grand_total = total_price + shipping_cost

    saved_address = None
    if request.user.is_authenticated:
        saved_address = SavedAddress.objects.filter(user=request.user).first()

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. خصم الكمية من المخزن
                for item in cart_items:
                    variant = ProductVariant.objects.select_for_update().get(id=item.variant.id)
                    if variant.stock < item.quantity:
                        raise ValueError(f"عفواً، الكمية المتاحة من {item.product.name_ar} مقاس {variant.size} لم تعد تكفي.")
                    variant.stock -= item.quantity
                    variant.save()

                # 2. إنشاء الطلب
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    full_name=request.POST.get('full_name'),
                    phone=request.POST.get('phone'),
                    email=request.POST.get('email'),
                    address=request.POST.get('address'),
                    building=request.POST.get('building'),
                    floor=request.POST.get('floor'),
                    apartment=request.POST.get('apartment'),
                    landmark=request.POST.get('landmark'),
                    region=request.POST.get('region'),
                    total_price=grand_total,
                    status='Pending'
                )

                logger.info(f"Order #{order.tracking_no} created by {order.full_name} ({order.phone}) — total: {grand_total} EGP")

                # 3. حفظ العنوان للمرات القادمة
                if request.user.is_authenticated:
                    address_record, _ = SavedAddress.objects.get_or_create(user=request.user)
                    address_record.phone = request.POST.get('phone')
                    address_record.region = request.POST.get('region')
                    address_record.address = request.POST.get('address')
                    address_record.building = request.POST.get('building')
                    address_record.floor = request.POST.get('floor')
                    address_record.apartment = request.POST.get('apartment')
                    address_record.landmark = request.POST.get('landmark')
                    address_record.save()

                # 4. إضافة المنتجات للطلب
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        variant=item.variant,
                        quantity=item.quantity,
                        price=item.product.base_price,
                    )

                # 5. مسح السلة والتحويل
                # (البريد الإلكتروني يُرسل تلقائياً عبر Signal في email_handlers.py)
                cart.delete()
                request.session.pop('cart_id', None)
                request.session['last_order_tracking'] = order.tracking_no
                request.session['last_order_id'] = order.id
                return redirect('order_success')

        except ValueError as e:
            logger.warning(f"Checkout failed — stock issue: {e}")
            messages.error(request, str(e))
            return redirect('cart_detail')

    egypt_provinces = sorted([
        'القاهرة', 'الجيزة', 'الإسكندرية', 'الدقهلية', 'الشرقية',
        'المنوفية', 'القليوبية', 'البحيرة', 'الغربية', 'بورسعيد',
        'دمياط', 'الإسماعيلية', 'السويس', 'كفر الشيخ', 'الفيوم',
        'بني سويف', 'المنيا', 'أسيوط', 'سوهاج', 'قنا',
        'الأقصر', 'أسوان', 'البحر الأحمر', 'الوادي الجديد',
        'مطروح', 'شمال سيناء', 'جنوب سيناء',
    ])

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
        'saved_address': saved_address,
        'provinces': egypt_provinces,
    })


# ============================================================
# صفحات ثابتة
# ============================================================
def return_policy(request):
    return render(request, 'store/return_policy.html')

def terms(request):
    return render(request, 'terms.html')

def about(request):
    return render(request, 'about.html')
