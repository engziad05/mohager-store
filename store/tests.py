import pytest
from cart.models import Cart, CartItem
from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from products.models import Category, Product, ProductVariant

User = get_user_model()


@pytest.mark.django_db
class TestCartModel:

    def test_create_guest_cart_and_add_item(self):
        """اختبار إنشاء سلة لزائر (بدون حساب) وإضافة منتج ليها"""
        category = Category.objects.create(
            name_ar='تيشيرتات', name_en='T-Shirts', slug='t-shirts'
        )
        product = Product.objects.create(
            category=category, name_ar='تيشيرت مُهاجر', name_en='Mohager T-Shirt', base_price=200.00
        )
        cart = Cart.objects.create()
        cart_item = CartItem.objects.create(cart=cart, product=product, quantity=2)

        assert cart.user is None
        assert cart.items.count() == 1
        assert cart_item.quantity == 2
        assert cart_item.product.name_en == 'Mohager T-Shirt'

    def test_create_user_cart(self):
        """اختبار إنشاء سلة مربوطة بعميل مسجل"""
        user = User.objects.create_user(username='ziad', password='password123')
        cart = Cart.objects.create(user=user)
        assert cart.user.username == 'ziad'

    def test_order_creation_and_stock_deduction(self):
        """اختبار إنشاء طلب وخصم المخزون"""
        category = Category.objects.create(
            name_ar='هوديز', name_en='Hoodies', slug='hoodies'
        )
        product = Product.objects.create(
            category=category, name_ar='هودي', name_en='Hoodie', base_price=400.00
        )
        variant = ProductVariant.objects.create(
            product=product, size='XL', stock=10
        )
        order = Order.objects.create(
            full_name='عميل تجريبي', phone='01000000000', address='القاهرة', total_price=900.00
        )
        quantity_bought = 2
        OrderItem.objects.create(
            order=order,
            product=product,
            variant=variant,
            quantity=quantity_bought,
            price=product.base_price,
        )

        variant.stock -= quantity_bought
        variant.save()
        variant.refresh_from_db()

        assert order.full_name == 'عميل تجريبي'
        assert order.items.count() == 1
        assert variant.stock == 8
