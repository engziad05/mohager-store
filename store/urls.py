from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    
    # رابط الإضافة للسلة اللي الزرار بيدور عليه
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    
    # رابط صفحة السلة نفسها
    path('cart/', views.cart_detail, name='cart_detail'),
    
    # روابط الحذف وتعديل الكمية جوه السلة
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('cart/update/<int:item_id>/<str:action>/', views.update_quantity, name='update_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('success/', views.order_success, name='order_success'),
    path('shop/', views.shop, name='shop'),
    path('cart/drawer/', views.cart_drawer, name='cart_drawer'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('return-policy/', views.return_policy, name='return_policy'),
    path('terms/', views.terms, name='terms'),
    path('about/', views.about, name='about'),
]
