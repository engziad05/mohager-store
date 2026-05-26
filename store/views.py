import json
import string
import urllib.request
import urllib.error

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django_ratelimit.decorators import ratelimit
from django.views.decorators.cache import cache_page

from common.cache import get_or_cache
from orders.models import Order
from orders.services.checkout import complete_storefront_checkout
from cart.models import Cart, CartItem
from products.models import Category, Product, ProductVariant
from products.services import assert_sufficient_variant_stock
from .forms import SavedAddressForm
from .models import HeroSlide, SavedAddress, StoreSetting


# ============================================================
# Cart helper — eliminates N+1 queries across all views
# ============================================================
def _get_cart_data(request):
    """Fetch cart info in a single optimized query. Returns dict with
    cart, cart_items (list), cart_count, and total_price."""
    cart_id = request.session.get('cart_id')
    if not cart_id:
        return {'cart': None, 'cart_items': [], 'cart_count': 0, 'total_price': 0}

    cart = Cart.objects.filter(id=cart_id).first()
    if not cart:
        return {'cart': None, 'cart_items': [], 'cart_count': 0, 'total_price': 0}

    items = list(
        CartItem.objects.filter(cart=cart)
        .select_related('product', 'variant')
    )
    cart_count = sum(item.quantity for item in items)
    total_price = sum(item.total_price for item in items)
    return {
        'cart': cart,
        'cart_items': items,
        'cart_count': cart_count,
        'total_price': total_price,
    }


# ============================================================
# الصفحة الرئيسية
# ============================================================
def index(request):
    # Cache featured products and hero slides — invalidated by signals
    products = get_or_cache(
        'index:products',
        lambda: list(
            Product.objects.filter(is_active=True)
            .select_related('category')
            .prefetch_related('variants', 'images')[:8]
        ),
        timeout=getattr(settings, 'CACHE_TIMEOUT_PRODUCT_LIST', 300),
    )
    slides = get_or_cache(
        'index:slides',
        lambda: list(HeroSlide.objects.filter(is_active=True).order_by('order')),
        timeout=getattr(settings, 'CACHE_TIMEOUT_HERO_SLIDES', 600),
    )

    cd = _get_cart_data(request)

    context = {
        'products': products,
        'slides': slides,
        'cart_count': cd['cart_count'],
        'cart_items': cd['cart_items'],
        'total_price': cd['total_price'],
    }
    return render(request, 'store/index.html', context)


# ============================================================
# صفحة المتجر
# ============================================================
def shop(request):
    query = request.GET.get('q', '')
    category_slug = request.GET.get('category', '')

    # Build a filter-aware cache key so different searches get separate entries
    cache_key = f"shop:products:{category_slug}:{query}"

    def _fetch_products():
        qs = Product.objects.filter(is_active=True).select_related('category').prefetch_related('variants', 'images')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if query:
            qs = qs.filter(
                Q(name_ar__icontains=query) |
                Q(name_en__icontains=query) |
                Q(description_ar__icontains=query)
            )
        return list(qs)

    products = get_or_cache(
        cache_key,
        _fetch_products,
        timeout=getattr(settings, 'CACHE_TIMEOUT_PRODUCT_LIST', 300),
    )

    # Cache categories list — invalidated by category signals
    categories = get_or_cache(
        'shop:categories',
        lambda: list(Category.objects.filter(is_active=True)),
        timeout=getattr(settings, 'CACHE_TIMEOUT_CATEGORY', 600),
    )

    cd = _get_cart_data(request)

    context = {
        'products': products,
        'categories': categories,
        'cart_count': cd['cart_count'],
    }
    return render(request, 'store/shop.html', context)


# ============================================================
# صفحة تفاصيل المنتج
# ============================================================
def product_detail(request, product_id):
    # Cache product detail with variants and images — invalidated by product/variant signals
    cache_key = f"product_detail:{product_id}"

    def _fetch_product():
        product = get_object_or_404(
            Product.objects.select_related('category').prefetch_related('variants', 'images'),
            id=product_id,
        )
        # Extract prefetched data while it's hot
        return {
            'product': product,
            'variants': list(product.variants.all()),
            'extra_images': list(product.images.all()),
        }

    cached = get_or_cache(
        cache_key,
        _fetch_product,
        timeout=getattr(settings, 'CACHE_TIMEOUT_PRODUCT_DETAIL', 600),
    )

    cd = _get_cart_data(request)

    context = {
        'product': cached['product'],
        'variants': cached['variants'],
        'extra_images': cached['extra_images'],
        'cart_count': cd['cart_count'],
    }
    return render(request, 'store/product_detail.html', context)


# ============================================================
# صفحة السلة
# ============================================================
def cart_detail(request):
    cd = _get_cart_data(request)
    shipping_cost = 0
    grand_total = 0

    if cd['total_price'] > 0:
        setting = get_or_cache(
            'store_settings',
            lambda: StoreSetting.objects.first(),
            timeout=getattr(settings, 'CACHE_TIMEOUT_STORE_SETTINGS', 3600),
        )
        shipping_cost = setting.shipping_cost if setting else 0
        grand_total = cd['total_price'] + shipping_cost

    context = {
        'cart': cd['cart'],
        'cart_items': cd['cart_items'],
        'total_price': cd['total_price'],
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
    messages.success(request, 'تم حذف القطعة من السلة 🗑️')
    return redirect('cart_detail')


# ============================================================
# تعديل الكمية
# ============================================================
def update_quantity(request, item_id, action):
    cart_id = request.session.get('cart_id')
    cart_item = get_object_or_404(CartItem, id=item_id, cart_id=cart_id)

    if action == 'increase':
        try:
            assert_sufficient_variant_stock(cart_item.variant, cart_item.quantity + 1)
        except ValueError:
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
        cart_items = list(
            CartItem.objects.filter(cart=cart)
            .select_related('product', 'variant')
        )
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
    cd = _get_cart_data(request)

    context = {
        'cart': cd['cart'],
        'cart_items': cd['cart_items'],
        'total_price': cd['total_price'],
        'grand_total': cd['total_price'],
        'cart_count': cd['cart_count'],
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

        try:
            assert_sufficient_variant_stock(variant, 1)
        except ValueError:
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
            try:
                assert_sufficient_variant_stock(variant, cart_item.quantity + 1)
            except ValueError:
                messages.error(request, f'عفواً، أقصى كمية متاحة من هذا المقاس هي {variant.stock} قطع!')
                return redirect('product_detail', product_id=product.id)
            cart_item.quantity += 1
            cart_item.save()

        if request.headers.get('HX-Request'):
            cart_items = list(
                CartItem.objects.filter(cart=cart)
                .select_related('product', 'variant')
            )
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

    cart_items = list(
        CartItem.objects.filter(cart=cart)
        .select_related('product', 'variant')
    )
    if not cart_items:
        return redirect('index')

    total_price = sum(item.total_price for item in cart_items)
    setting = get_or_cache(
        'store_settings',
        lambda: StoreSetting.objects.first(),
        timeout=getattr(settings, 'CACHE_TIMEOUT_STORE_SETTINGS', 3600),
    )
    shipping_cost = setting.shipping_cost if setting else 0
    grand_total = total_price + shipping_cost

    saved_address = None
    if request.user.is_authenticated:
        saved_address = SavedAddress.objects.filter(user=request.user).first()

    if request.method == 'POST':
        try:
            order = complete_storefront_checkout(
                cart=cart,
                cart_items=cart_items,
                user=request.user,
                post_data=request.POST,
                grand_total=grand_total,
            )
            request.session.pop('cart_id', None)
            request.session['last_order_tracking'] = order.tracking_no
            request.session['last_order_id'] = order.id
            return redirect('order_success')

        except ValueError as e:
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
