from django.contrib import admin
from .models import Category, Product, ProductVariant

# تغيير عنوان لوحة التحكم من فوق عشان تليق بمهاجر
admin.site.site_header = "إدارة متجر مُهاجر"
admin.site.site_title = "مُهاجر"

# تسجيل الجداول
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductVariant)