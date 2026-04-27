from django.shortcuts import render
from .models import Product # استدعاء جدول المنتجات

def home(request):
    # هات كل المنتجات اللي حالتها Active
    products = Product.objects.filter(is_active=True)
    
    # ابعت المنتجات دي لصفحة الـ HTML تحت اسم 'products'
    context = {
        'products': products
    }
    return render(request, 'store/index.html', context)