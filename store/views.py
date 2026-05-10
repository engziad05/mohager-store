from django_ratelimit.decorators import ratelimit
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from .models import Product, HeroSlide, ProductVariant, Cart, CartItem, Order, OrderItem, Category, ProductImage
from django.db import transaction
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from .forms import SavedAddressForm
from .models import  SavedAddress
from django.shortcuts import get_object_or_404
import threading
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
import json
import urllib.request
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
import threading
import urllib.request
import json
from django.conf import settings
from .models import StoreSetting



def index(request):
    products = Product.objects.filter(is_active=True)[:8]
    slides = HeroSlide.objects.filter(is_active=True).order_by('order')
    
    cart_id = request.session.get('cart_id')
    cart_count = 0
    
    # عرفنا المتغيرات دي هنا فاضية عشان الإيرور ميظهرش لو السلة فاضية
    cart_items = []
    total_price = 0

    if cart_id:
        cart = Cart.objects.filter(id=cart_id).first()
        if cart:
            cart_items = CartItem.objects.filter(cart=cart)
            cart_count = sum(item.quantity for item in cart_items)
            total_price = sum(item.total_price for item in cart_items)
            
    context = {
        'products': products,
        'slides': slides,
        'cart_count': cart_count,
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'store/index.html', context)

def shop(request):
    # صفحة المتجر اللي فيها البحث والفلترة 
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)

    query = request.GET.get('q')
    category_slug = request.GET.get('category')

    # الفلترة بالقسم
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    # البحث بالاسم أو الوصف
    if query:
        products = products.filter(
            Q(name_ar__icontains=query) | 
            Q(name_en__icontains=query) | 
            Q(description_ar__icontains=query)
        )

    # حساب عدد المنتجات في السلة
    cart_id = request.session.get('cart_id')
    cart_count = 0
    if cart_id:
        cart = Cart.objects.filter(id=cart_id).first()
        if cart:
            cart_count = sum(item.quantity for item in CartItem.objects.filter(cart=cart))

    context = {
        'products': products,
        'categories': categories,
        'cart_count': cart_count,
    }
    return render(request, 'store/shop.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variants = ProductVariant.objects.filter(product=product)
    extra_images = ProductImage.objects.filter(product=product)

    # حساب عدد المنتجات في السلة
    cart_id = request.session.get('cart_id')
    cart_count = 0
    if cart_id:
        cart = Cart.objects.filter(id=cart_id).first()
        if cart:
            cart_count = sum(item.quantity for item in CartItem.objects.filter(cart=cart))

    context = {
        'product': product,
        'variants': variants,
        'extra_images': extra_images,
        'cart_count': cart_count,
    }
    return render(request, 'store/product_detail.html', context)



def cart_detail(request):
    cart_id = request.session.get('cart_id')
    cart = None
    cart_items = []
    total_price = 0
    grand_total = 0 
    
    if cart_id:
        cart = Cart.objects.filter(id=cart_id).first()
        if cart:
            cart_items = CartItem.objects.filter(cart=cart)
            total_price = sum(item.total_price for item in cart_items)
    
    if total_price > 0:
        grand_total = total_price
            
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
        'grand_total': grand_total,
        'grand_total': grand_total, 
    }
    return render(request, 'store/cart.html', context)

def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    messages.success(request, 'تم حذف القطعة من السلة 🗑️')
    return redirect('cart_detail')

def update_quantity(request, item_id, action):
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    if action == 'increase':
        # 🛑 الحماية التالتة: نمنعه يزود الكمية في السلة لو خلصت من المخزن
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
            
    # لو الطلب جاي من HTMX (عشان الدرج)
    if request.headers.get('HX-Request'):
        cart = cart_item.cart
        cart_items = CartItem.objects.filter(cart=cart)
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


    
def order_success(request):
    return render(request, 'store/order_success.html')
def cart_drawer(request):
    cart_id = request.session.get('cart_id')
    cart = None
    cart_items = []
    total_price = 0
    grand_total = 0 
    cart_count = 0 # <-- ضفنا دي عشان نحدث الرقم

    if cart_id:
        cart = Cart.objects.filter(id=cart_id).first()
        if cart:
            cart_items = CartItem.objects.filter(cart=cart)
            total_price = sum(item.total_price for item in cart_items)
            grand_total = total_price
            cart_count = sum(item.quantity for item in cart_items) # <-- بنحسب عدد القطع
            
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
        'grand_total': grand_total, 
        'cart_count': cart_count, # <-- بعتناها للـ HTML
    }
    return render(request, 'store/partials/cart_items.html', context)


def add_to_cart(request, product_id):
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        
        if not variant_id:
            messages.error(request, 'من فضلك اختر المقاس أولاً!')
            return redirect('product_detail', product_id=product_id)

        product = get_object_or_404(Product, id=product_id)
        variant = get_object_or_404(ProductVariant, id=variant_id)

        # 🛑 الحماية الأولى: التأكد من وجود مخزون أصلاً
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
        
        # 🛑 الحماية التانية: التأكد إن الكمية المطلوبة مش هتعدي المخزون
        if not created:
            if cart_item.quantity + 1 > variant.stock:
                messages.error(request, f'عفواً، أقصى كمية متاحة من هذا المقاس هي {variant.stock} قطع!')
                return redirect('product_detail', product_id=product.id)
            
            cart_item.quantity += 1
            cart_item.save()

        # كود الـ HTMX بتاعنا زي ما هو
        if request.headers.get('HX-Request'):
            cart_items = CartItem.objects.filter(cart=cart)
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



@login_required(login_url='/accounts/login/')
def dashboard(request):
    # سحبنا الأوردرات بالـ user ورتبناها بـ created_at
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders
    }
    return render(request, 'dashboard.html', context)
@login_required(login_url='/accounts/login/')
def dashboard(request):
    # 1. بنجيب الأوردرات زي ما عملنا قبل كده
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # 2. بنحاول نجيب عنوان العميل لو كان مسجله قبل كده
    try:
        saved_address = request.user.saved_address
    except SavedAddress.DoesNotExist:
        saved_address = None

    # 3. لو العميل داس على زرار "حفظ العنوان"
    if request.method == 'POST':
        form = SavedAddressForm(request.POST, instance=saved_address)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user # بنربط العنوان بالعميل اللي فاتح الحساب
            address.save()
            # هنا ممكن نضيف رسالة نجاح بعدين
    else:
        # لو دي أول مرة يفتح الصفحة، بنعرضله الفورم (فاضية أو فيها بياناته القديمة)
        form = SavedAddressForm(instance=saved_address)
    
    context = {
        'orders': orders,
        'form': form, # بعتنا الفورم للـ HTML
    }
    return render(request, 'dashboard.html', context)

@login_required(login_url='/accounts/login/')
def order_detail(request, order_id):
    # بنجيب الأوردر، ولازم نتأكد إنه يخص العميل اللي مسجل دخول عشان محدش يشوف أوردرات غيره
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'order_detail.html', context)

@ratelimit(key='ip', rate='5/m', block=True)
def checkout(request):
    cart_id = request.session.get('cart_id')
    
    if not cart_id:
        return redirect('index')
        
    cart = Cart.objects.filter(id=cart_id).first()
    if not cart:
        return redirect('index')
        
    cart_items = CartItem.objects.filter(cart=cart)
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
                    total_price=total_price,
                    status='Pending' 
                )
                
                # 3. حفظ العنوان للمرات القادمة
                if request.user.is_authenticated:
                    address_record, created = SavedAddress.objects.get_or_create(user=request.user)
                    address_record.phone = request.POST.get('phone')
                    address_record.region = request.POST.get('region')
                    address_record.address = request.POST.get('address')
                    address_record.building = request.POST.get('building')
                    address_record.floor = request.POST.get('floor')
                    
                    # دالة بتبعت الإيميل عن طريق الـ API من ورا ضهر Railway
                    def send_bg_email_api(to_email, html, order_id):
                        url = "https://api.brevo.com/v3/smtp/email"
                        # بنسحب الباسورد بتاع برافو لأنه هو هو الـ API Key
                        api_key = str(settings.EMAIL_HOST_PASSWORD).strip()
                        
                        data = {
                            "sender": {"name": "Mohager Store", "email": settings.DEFAULT_FROM_EMAIL},
                            "to": [{"email": to_email}],
                            "subject": f"تأكيد طلبك بنجاح من مُهاجر - رقم #{order_id}",
                            "htmlContent": html
                        }
                        
                        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'))
                        req.add_header('accept', 'application/json')
                        req.add_header('api-key', api_key)
                        req.add_header('content-type', 'application/json')
                        
                        try:
                            with urllib.request.urlopen(req) as response:
                                print("✅✅✅ تم إرسال الإيميل بنجاح عن طريق API! ✅✅✅")
                        except Exception as e:
                            print(f"❌❌❌ مشكلة في الـ API: {e} ❌❌❌")

                    # تشغيل الإرسال في الخلفية
                    try:
                        email_thread = threading.Thread(target=send_bg_email_api, args=(order.email, html_content, order.id))
                        email_thread.start()
                    except Exception as e:
                        print(f"Error starting email thread: {e}")
                cart.delete()
                if 'cart_id' in request.session:
                    del request.session['cart_id']

                return redirect('order_success')
                
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('cart_detail')

    egypt_provinces = sorted(['القاهرة', 'الجيزة', 'الإسكندرية', 'الدقهلية', 'الشرقية', 'المنوفية', 'القليوبية', 'البحيرة', 'الغربية', 'بورسعيد', 'دمياط', 'الإسماعيلية', 'السويس', 'كفر الشيخ', 'الفيوم', 'بني سويف', 'المنيا', 'أسيوط', 'سوهاج', 'قنا', 'الأقصر', 'أسوان', 'البحر الأحمر', 'الوادي الجديد', 'مطروح', 'شمال سيناء', 'جنوب سيناء'])

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'shipping_cost': shipping_cost,  # بعتنا سعر الشحن
        'grand_total': grand_total,      # بعتنا الإجمالي النهائي
        'saved_address': saved_address,
        'provinces': egypt_provinces,
    })
def return_policy(request):
    return render(request, 'store/return_policy.html')
def terms(request):
    return render(request, 'terms.html')
def about(request):
    return render(request, 'about.html')


