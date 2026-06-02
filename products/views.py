from django.conf import settings
from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Category, Product
from .serializers import ProductSerializer, CategorySerializer
from common.cache import CachedViewSetMixin, get_or_cache
from common.permissions import IsAdminOrReadOnly


class ProductViewSet(CachedViewSetMixin, viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category__slug', 'is_active']
    search_fields = ['name_ar', 'name_en', 'description_ar', 'description_en']
    ordering_fields = ['created_at', 'base_price']
    ordering = ['-created_at']
    cache_timeout = getattr(settings, 'CACHE_TIMEOUT_PRODUCT_LIST', 300)
    cache_key_prefix = 'api:products'

    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """Return related products in the same category, cached per product."""
        product = self.get_object()
        cache_key = f"api:products:related:{pk}"

        def _fetch():
            related_qs = Product.objects.filter(
                category=product.category, is_active=True
            ).select_related('category').prefetch_related('images').exclude(pk=product.pk)[:5]
            serializer = self.get_serializer(related_qs, many=True)
            return Response(serializer.data)

        return get_or_cache(cache_key, _fetch, timeout=self.cache_timeout)


class CategoryViewSet(CachedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    cache_timeout = getattr(settings, 'CACHE_TIMEOUT_CATEGORY', 600)
    cache_key_prefix = 'api:categories'
