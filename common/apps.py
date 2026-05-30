from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'

    def ready(self):
        # Fix django-unfold 0.81.0 bug with Django 5.0+ contexts
        from django.template.context import Context
        def safe_flatten(self):
            flat = {}
            for d in self.dicts:
                if isinstance(d, dict):
                    flat.update(d)
                elif hasattr(d, 'keys'):
                    for k in d.keys():
                        flat[k] = d[k]
            return flat
        Context.flatten = safe_flatten

        from django.contrib.admin.sites import AlreadyRegistered

        from accounts.admin import CustomUserAdmin, StaffUserAdmin
        from accounts.models import CustomUser, StaffUser
        from cart.admin import CartAdmin
        from cart.models import Cart
        from common.admin import mohager_admin
        from orders.admin import OrderAdmin
        from orders.models import Order
        from products.admin import CategoryAdmin, ProductAdmin
        from products.models import Category, Product
        from store.admin import HeroSlideAdmin, StoreSettingAdmin
        from store.models import HeroSlide, StoreSetting

        for model, admin_class in (
            (CustomUser, CustomUserAdmin),
            (StaffUser, StaffUserAdmin),
            (Product, ProductAdmin),
            (Category, CategoryAdmin),
            (Order, OrderAdmin),
            (HeroSlide, HeroSlideAdmin),
            (Cart, CartAdmin),
            (StoreSetting, StoreSettingAdmin),
        ):
            try:
                mohager_admin.register(model, admin_class)
            except AlreadyRegistered:
                pass
