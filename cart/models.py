from django.conf import settings
from django.db import models

from products.models import Product, MasterStockVariant


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'store_cart'

    def __str__(self):
        return f'سلة رقم {self.id}'

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey('products.MasterStockVariant', on_delete=models.SET_NULL, null=True)
    product_color = models.ForeignKey('products.ProductColor', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'store_cartitem'

    def __str__(self):
        return f'{self.quantity} x {self.product.name_en}'

    @property
    def total_price(self):
        item_price = self.product.base_price
        if self.product_color and self.product_color.price is not None:
            item_price = self.product_color.price
        return item_price * self.quantity
