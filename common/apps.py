from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'

    def ready(self):
        from django.contrib.admin.sites import AlreadyRegistered

        from accounts.admin import CustomUserAdmin
        from accounts.models import CustomUser
        from common.admin import mohager_admin
        from store.admin import (
            CartAdmin,
            CategoryAdmin,
            HeroSlideAdmin,
            OrderAdmin,
            ProductAdmin,
            StoreSettingAdmin,
        )
        from store.models import Cart, Category, HeroSlide, Order, Product, StoreSetting

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
