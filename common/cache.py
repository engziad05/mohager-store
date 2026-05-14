from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from functools import wraps
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


# ============================================================
# Cache Key Helpers
# ============================================================

def make_cache_key(prefix, *parts):
    """
    Build a consistent cache key from a prefix and arbitrary parts.
    Non-string parts are JSON-serialized; all parts are joined with ':'.
    """
    key_parts = [prefix]
    for part in parts:
        if isinstance(part, str):
            key_parts.append(part)
        else:
            key_parts.append(hashlib.md5(
                json.dumps(part, sort_keys=True).encode()
            ).hexdigest())
    return ':'.join(key_parts)


def make_query_cache_key(func_name, args, kwargs, key_prefix=None):
    """
    Generate a deterministic cache key from function name + args + kwargs.
    """
    key_data = {
        'func': func_name,
        'args': str(args),
        'kwargs': str(sorted(kwargs.items())),
    }
    key_hash = hashlib.md5(
        json.dumps(key_data, sort_keys=True).encode()
    ).hexdigest()
    return f"{key_prefix or 'query'}:{key_hash}"


# ============================================================
# Core Utility: get_or_cache
# ============================================================

def get_or_cache(key, func, timeout=300):
    """
    Retrieve from cache, or execute func(), store the result, and return it.

    Args:
        key: Cache key string.
        func: Callable returning the value to cache on miss.
        timeout: Cache TTL in seconds.

    Returns:
        The cached or freshly computed value.
    """
    result = cache.get(key)
    if result is not None:
        return result

    result = func()
    cache.set(key, result, timeout)
    return result


# ============================================================
# Decorators
# ============================================================

def cache_query_result(timeout=300, key_prefix=None):
    """
    Decorator to cache the return value of any function.

    Args:
        timeout: Cache timeout in seconds (default: 5 minutes).
        key_prefix: Custom prefix for the cache key.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = make_query_cache_key(func.__name__, args, kwargs, key_prefix)
            result = cache.get(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator


def cache_product_list(timeout=300):
    """
    Decorator to cache product list queries.
    Cache key includes positional and keyword arguments so different
    filter combinations get separate cache entries.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = make_cache_key(
                'product_list',
                str(args),
                str(sorted(kwargs.items())),
            )
            result = cache.get(cache_key)

            if result is not None:
                return result

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator


def cache_product_detail(timeout=600):
    """
    Decorator to cache individual product detail lookups.
    Works with function-based views where product_id is a keyword or
    positional argument (NOT a class-based view `self`).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            product_id = kwargs.get('product_id') or kwargs.get('pk')
            if not product_id and args:
                # Skip the request argument (first arg in FBV)
                for arg in args[1:]:
                    if isinstance(arg, int):
                        product_id = arg
                        break

            if product_id:
                cache_key = f"product_detail:{product_id}"
                result = cache.get(cache_key)

                if result is not None:
                    return result

                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
                return result

            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================
# DRF ViewSet Cache Mixin
# ============================================================

class CachedViewSetMixin:
    """
    Mixin for DRF ViewSets that caches read operations (list, retrieve)
    and automatically invalidates cache on write operations.

    Subclasses can override:
        cache_timeout       – TTL in seconds (default 300)
        cache_key_prefix    – prefix for cache keys (default 'api')
    """
    cache_timeout = 300
    cache_key_prefix = 'api'

    def _get_list_cache_key(self, request):
        """Build a cache key for list endpoints including query params."""
        query_string = request.META.get('QUERY_STRING', '')
        path = request.META.get('PATH_INFO', '')
        key_hash = hashlib.md5(f"{path}?{query_string}".encode()).hexdigest()
        return f"{self.cache_key_prefix}:list:{key_hash}"

    def _get_detail_cache_key(self, pk):
        """Build a cache key for detail/retrieve endpoints."""
        return f"{self.cache_key_prefix}:detail:{pk}"

    def list(self, request, *args, **kwargs):
        cache_key = self._get_list_cache_key(request)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response, self.cache_timeout)
        return response

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if pk:
            cache_key = self._get_detail_cache_key(pk)
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        response = super().retrieve(request, *args, **kwargs)

        if pk:
            cache_key = self._get_detail_cache_key(pk)
            cache.set(cache_key, response, self.cache_timeout)
        return response

    def perform_create(self, serializer):
        super().perform_create(serializer)
        self._invalidate_list_cache()

    def perform_update(self, serializer):
        super().perform_update(serializer)
        pk = serializer.instance.pk
        self._invalidate_detail_cache(pk)
        self._invalidate_list_cache()

    def perform_destroy(self, instance):
        pk = instance.pk
        super().perform_destroy(instance)
        self._invalidate_detail_cache(pk)
        self._invalidate_list_cache()

    def _invalidate_list_cache(self):
        """Delete all list cache entries for this viewset."""
        try:
            cache.delete_pattern(f"{self.cache_key_prefix}:list:*")
        except (AttributeError, Exception):
            logger.debug("Pattern deletion not available for cache list invalidation")

    def _invalidate_detail_cache(self, pk):
        """Delete the detail cache entry for a specific object."""
        cache.delete(f"{self.cache_key_prefix}:detail:{pk}")


# ============================================================
# Cache Invalidation Helpers
# ============================================================

def invalidate_product_cache(product_id):
    """
    Invalidate all cache entries related to a specific product.
    Called from signals when a Product or ProductVariant is saved/deleted.
    """
    # Detail page for this product (FBV store view)
    cache.delete(f"product_detail:{product_id}")

    # API detail and related endpoints for this product
    cache.delete(f"api:products:detail:{product_id}")
    cache.delete(f"api:products:related:{product_id}")

    # All product list / shop / API list caches
    _delete_pattern("product_list:*")
    _delete_pattern("shop:*")
    _delete_pattern("api:products:list:*")

    # Homepage (featured products may include this one)
    cache.delete("index:products")
    cache.delete("index:slides")

    logger.debug("Invalidated product cache for product_id=%s", product_id)


def invalidate_category_cache(category_slug=None):
    """
    Invalidate all cache entries related to categories.
    When category_slug is provided, also invalidates category-specific lists.
    """
    _delete_pattern("product_list:*")
    _delete_pattern("shop:*")
    _delete_pattern("api:products:list:*")
    _delete_pattern("api:categories:*")
    cache.delete("shop:categories")

    if category_slug:
        _delete_pattern(f"shop:*{category_slug}*")

    logger.debug("Invalidated category cache (slug=%s)", category_slug)


def invalidate_hero_cache():
    """Invalidate hero slide cache entries."""
    cache.delete("index:slides")
    _delete_pattern("hero_slides:*")
    logger.debug("Invalidated hero slide cache")


def invalidate_store_settings_cache():
    """Invalidate store settings cache."""
    cache.delete("store_settings")
    logger.debug("Invalidated store settings cache")


def invalidate_all_product_cache():
    """
    Nuclear option — clear every product/category/shop/index related cache.
    Useful after bulk admin actions.
    """
    _delete_pattern("product_*")
    _delete_pattern("shop:*")
    _delete_pattern("index:*")
    _delete_pattern("api:*")
    _delete_pattern("category_*")
    _delete_pattern("hero_slides:*")
    cache.delete("store_settings")
    cache.delete("shop:categories")
    logger.debug("Invalidated ALL product-related cache")


# ============================================================
# Internal Helpers
# ============================================================

def _delete_pattern(pattern):
    """
    Safely delete cache keys matching a pattern.
    Uses django-redis delete_pattern; silently skips if unavailable.
    """
    try:
        cache.delete_pattern(pattern)
    except (AttributeError, Exception):
        logger.debug("Pattern deletion unavailable for pattern: %s", pattern)
