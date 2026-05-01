from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, HeroSlide, ProductVariant, Cart, CartItem, Order, OrderItem
from django.contrib import messages

def index(request):
    products = Product.objects.all()
    slides = HeroSlide.objects.filter(is_active=True).order_by('order')

    # --- الكود الجديد لعد المنتجات في السلة ---
    cart_id = request.session.get('cart_id')
    cart_count = 0
    if cart_id:
        cart = Cart.objects.filter(id=cart_id).first()
        if cart:
            # هنا استخدمنا الفلتر المباشر والمضمون 100%
            cart_items = CartItem.objects.filter(cart=cart)
            cart_count = sum(item.quantity for item in cart_items)
    # ----------------------------------------

    context = {
        'products': products,
        'slides': slides,
        'cart_count': cart_count,
    }
    return render(request, 'store/index.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # السطر ده بيجيب كل المقاسات المربوطة بالتيشيرت ده بس
    variants = ProductVariant.objects.filter(product=product)

    # --- الكود الجديد لعد المنتجات في السلة ---
    cart_id = request.session.get('cart_id')
    cart_count = 0
    if cart_id:
        cart = Cart.objects.filter(id=cart_id).first()
        if cart:
            cart_items = CartItem.objects.filter(cart=cart)
            cart_count = sum(item.quantity for item in cart_items)
    # ----------------------------------------

    context = {
        'product': product,
        'variants': variants,
        'cart_count': cart_count, # بعتنا العدد للصفحة
    }
    return render(request, 'store/product_detail.html', context)

def add_to_cart(request, product_id):
    if request.method == 'POST':
        # 1. نستلم رقم المقاس اللي الجافاسكريبت بعته
        variant_id = request.POST.get('variant_id')
        product = get_object_or_404(Product, id=product_id)
        variant = get_object_or_404(ProductVariant, id=variant_id)
        
        # 2. نشوف لو الزبون ده ليه سلة شغالة، لو ملوش نفتحله سلة جديدة
        cart_id = request.session.get('cart_id')
        if cart_id:
            cart = Cart.objects.filter(id=cart_id).first()
            if not cart:
                cart = Cart.objects.create()
                request.session['cart_id'] = cart.id
        else:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
            
        # 3. نحط التيشيرت بالمقاس في السلة
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, 
            product=product, 
            variant=variant,
        )
        
        # لو التيشيرت بنفس المقاس موجود قبل كده، نزود الكمية بس
        if not created:
            cart_item.quantity += 1
            cart_item.save()
            
        # السطر الجديد بتاع رسالة النجاح
        messages.success(request, 'تم إضافة القطعة للسلة بنجاح! 🛒')
        
        # 4. نرجعه تاني لصفحة التيشيرت
        return redirect('product_detail', product_id=product.id)
        
    return redirect('index')
def cart_detail(request):
    cart_id = request.session.get('cart_id')
    cart = None
    cart_items = []
    total_price = 0  # ثمن المنتجات بس
    grand_total = 0 # الإجمالي النهائي
    
    if cart_id:
        cart = Cart.objects.filter(id=cart_id).first()
        if cart:
            cart_items = CartItem.objects.filter(cart=cart)
            for item in cart_items:
                total_price += item.product.price * item.quantity
    
    # الإجمالي النهائي هو هو المجموع الفرعي (لغينا الشحن خالص)
    if total_price > 0:
        grand_total = total_price
    else:
        grand_total = 0
            
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
        'grand_total': grand_total, 
    }
    return render(request, 'store/cart.html', context)

# دالة الحذف الجديدة
def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    messages.success(request, 'تم حذف القطعة من السلة 🗑️')
    return redirect('cart_detail')

def update_quantity(request, item_id, action):
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            # لو الكمية 1 وهو داس ناقص (-)، هنمسح التيشيرت خالص من السلة
            cart_item.delete()
            messages.success(request, 'تم حذف القطعة من السلة 🗑️')
            
    return redirect('cart_detail')
# الفنكشن الجديدة بتاعت الدفع (على الحرف خالص أهي)
def checkout(request):
    cart_id = request.session.get('cart_id')
    
    # الثلاث سطور دول عشان لو السلة فاضية يرجعه للرئيسية (ماتغيرهمش)
    if not cart_id:
        return redirect('index')
        
    cart = Cart.objects.filter(id=cart_id).first()
    if not cart:
        return redirect('index')
        
    cart_items = CartItem.objects.filter(cart=cart)
    if not cart_items.exists():
        return redirect('index')

    total_price = sum(item.product.price * item.quantity for item in cart_items)
    
    if request.method == 'POST':
        # تسجيل الأوردر
        order = Order.objects.create(
            full_name=request.POST.get('full_name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            address=request.POST.get('address'),
            building=request.POST.get('building'),
            floor=request.POST.get('floor'),
            apartment=request.POST.get('apartment'),
            landmark=request.POST.get('landmark'),
            region=request.POST.get('region'),
            total_price=total_price
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                quantity=item.quantity,
                price=item.product.price
            )
        
        # مسح السلة
        cart.delete()
        if 'cart_id' in request.session:
            del request.session['cart_id']

        # السطر ده هو اللي هيحدفه على صفحة النجاح الفخمة اللي عملناها!
        return redirect('order_success')

    egypt_provinces = sorted(['القاهرة', 'الجيزة', 'الإسكندرية', 'الدقهلية', 'الشرقية', 'المنوفية', 'القليوبية', 'البحيرة', 'الغربية', 'بورسعيد', 'دمياط', 'الإسماعيلية', 'السويس', 'كفر الشيخ', 'الفيوم', 'بني سويف', 'المنيا', 'أسيوط', 'سوهاج', 'قنا', 'الأقصر', 'أسوان', 'البحر الأحمر', 'الوادي الجديد', 'مطروح', 'شمال سيناء', 'جنوب سيناء'])

    return render(request, 'store/checkout.html', {
        'total_price': total_price,
        'provinces': egypt_provinces
    })
    
def order_success(request):
    return render(request, 'store/order_success.html')
    