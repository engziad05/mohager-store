from django.db.models import Sum, Count, Q
from django.utils import timezone

from unfold.admin import AdminSite

from store.models import Order, Product, Category, HeroSlide, StoreSetting
from accounts.models import CustomUser


class MohagerAdminSite(AdminSite):
    """Custom admin site with dashboard metrics for Mohager Store."""
    site_header = 'مُهاجر ستور — لوحة التحكم'
    site_title = 'مُهاجر ستور'
    index_title = 'لوحة التحكم'

    def index(self, request, extra_context=None):
        """Override index to inject dashboard metrics."""
        extra_context = extra_context or {}

        today = timezone.now().date()
        thirty_days_ago = today - timezone.timedelta(days=30)

        # ── Metric Cards ──────────────────────────────────────
        orders_qs = Order.objects.all()
        total_orders = orders_qs.count()
        total_sales = orders_qs.aggregate(
            total=Sum('total_price')
        )['total'] or 0

        # Orders in last 30 days
        recent_orders = orders_qs.filter(created_at__date__gte=thirty_days_ago)
        recent_orders_count = recent_orders.count()
        recent_sales = recent_orders.aggregate(
            total=Sum('total_price')
        )['total'] or 0

        active_products = Product.objects.filter(is_active=True).count()
        total_customers = CustomUser.objects.count()

        # Orders by status
        orders_by_status = dict(
            orders_qs.values_list('status').annotate(
                count=Count('id')
            )
        )

        extra_context.update({
            'total_orders': total_orders,
            'total_sales': total_sales,
            'recent_orders_count': recent_orders_count,
            'recent_sales': recent_sales,
            'active_products': active_products,
            'total_customers': total_customers,
            'orders_by_status': orders_by_status,
            'latest_orders': orders_qs.select_related('user').order_by('-created_at')[:10],
            'low_stock_products': Product.objects.filter(
                is_active=True,
                variants__stock__lt=5,
            ).distinct().select_related('category')[:5],
        })

        return super().index(request, extra_context)


# Singleton instance used across all admin.py files
mohager_admin = MohagerAdminSite(name='mohager_admin')
