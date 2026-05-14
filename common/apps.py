from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'

    def ready(self):
        from django.contrib.admin.sites import AlreadyRegistered

        from accounts.admin import CustomUserAdmin
        from accounts.models import CustomUser
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
