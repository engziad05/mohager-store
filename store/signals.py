from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from allauth.account.signals import user_logged_in

from common.cache import (
    invalidate_product_cache,
    invalidate_category_cache,
    invalidate_hero_cache,
    invalidate_store_settings_cache,
)
from .models import (
    Cart, CartItem, Category, HeroSlide,
    Product, ProductVariant, StoreSetting,
)


# ============================================================
# Cart merge on login (existing signal)
# ============================================================

@receiver(user_logged_in)
def merge_carts_on_login(request, user, **kwargs):
    """Merge guest session cart into the authenticated user's cart."""
    session_cart_id = request.session.get('cart_id')

    if session_cart_id:
        try:
            guest_cart = Cart.objects.get(id=session_cart_id, user__isnull=True)
            user_cart, created = Cart.objects.get_or_create(user=user)

            for item in guest_cart.items.all():
                user_item, item_created = CartItem.objects.get_or_create(
                    cart=user_cart,
                    product=item.product,
                    variant=item.variant,
                    defaults={'quantity': item.quantity}
                )
                if not item_created:
                    user_item.quantity += item.quantity
                    user_item.save()

            guest_cart.delete()
            request.session['cart_id'] = user_cart.id

        except Cart.DoesNotExist:
            pass


# ============================================================
# Cache Invalidation Signals
# ============================================================

@receiver(post_save, sender=Product)
def on_product_save(sender, instance, **kwargs):
    """Invalidate product and list caches when a product is created or updated."""
    invalidate_product_cache(instance.pk)


@receiver(post_delete, sender=Product)
def on_product_delete(sender, instance, **kwargs):
    """Invalidate product and list caches when a product is deleted."""
    invalidate_product_cache(instance.pk)


@receiver(post_save, sender=Category)
def on_category_save(sender, instance, **kwargs):
    """Invalidate category and product list caches when a category is saved."""
    invalidate_category_cache(instance.slug)


@receiver(post_delete, sender=Category)
def on_category_delete(sender, instance, **kwargs):
    """Invalidate category and product list caches when a category is deleted."""
    invalidate_category_cache(instance.slug)


@receiver(post_save, sender=ProductVariant)
def on_variant_save(sender, instance, **kwargs):
    """
    Invalidate the parent product's detail cache when a variant changes.
    Stock updates are the most common trigger here.
    """
    invalidate_product_cache(instance.product_id)


@receiver(post_delete, sender=ProductVariant)
def on_variant_delete(sender, instance, **kwargs):
    """Invalidate the parent product's detail cache when a variant is deleted."""
    invalidate_product_cache(instance.product_id)


@receiver(post_save, sender=HeroSlide)
def on_heroslide_save(sender, instance, **kwargs):
    """Invalidate hero slide cache when a slide is created or updated."""
    invalidate_hero_cache()


@receiver(post_delete, sender=HeroSlide)
def on_heroslide_delete(sender, instance, **kwargs):
    """Invalidate hero slide cache when a slide is deleted."""
    invalidate_hero_cache()


@receiver(post_save, sender=StoreSetting)
def on_storesetting_save(sender, instance, **kwargs):
    """Invalidate store settings cache when settings change."""
    invalidate_store_settings_cache()
