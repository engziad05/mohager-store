from datetime import timedelta

from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.db.models import Count, Min, Sum
from django.db.models.functions import TruncDate
from django.urls import reverse
from django.utils import timezone
from unfold.sites import UnfoldAdminSite


class MohagerAdminSite(UnfoldAdminSite):
    """Custom admin site with ecommerce dashboard metrics."""

    site_header = 'Mohager Store - Control Center'
    site_title = 'Mohager Store'
    index_title = 'Dashboard'

    def index(self, request, extra_context=None):
        """Inject optimized dashboard context for the custom admin homepage."""
        from orders.models import Order
        from products.models import Product

        extra_context = extra_context or {}

        today = timezone.now().date()
        chart_start = today - timedelta(days=13)
        thirty_days_ago = today - timedelta(days=30)

        orders_qs = Order.objects.select_related('user')
        product_qs = Product.objects.select_related('category').prefetch_related('variants')
        user_qs = get_user_model().objects.all()

        total_orders = orders_qs.count()
        total_revenue = orders_qs.aggregate(total=Sum('total_price'))['total'] or 0
        pending_orders = orders_qs.filter(status='Pending').count()
        products_count = product_qs.count()
        total_users = user_qs.count()

        recent_orders_qs = orders_qs.filter(created_at__date__gte=thirty_days_ago)
        recent_orders_count = recent_orders_qs.count()
        recent_revenue = recent_orders_qs.aggregate(total=Sum('total_price'))['total'] or 0

        orders_by_status = list(
            orders_qs.values('status')
            .annotate(count=Count('id'), revenue=Sum('total_price'))
            .order_by('status')
        )
        status_total = sum(item['count'] for item in orders_by_status) or 1
        status_labels = {
            'Pending': 'Pending',
            'Processing': 'Processing',
            'Shipped': 'Shipped',
            'Delivered': 'Delivered',
            'Cancelled': 'Cancelled',
        }
        for item in orders_by_status:
            item['label'] = status_labels.get(item['status'], item['status'])
            item['percent'] = round((item['count'] / status_total) * 100)

        raw_chart = {
            item['day']: item
            for item in orders_qs.filter(created_at__date__gte=chart_start)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(orders=Count('id'), revenue=Sum('total_price'))
            .order_by('day')
        }
        max_chart_revenue = max([item['revenue'] or 0 for item in raw_chart.values()] + [1])
        revenue_chart = []
        for offset in range(14):
            day = chart_start + timedelta(days=offset)
            item = raw_chart.get(day, {})
            revenue = item.get('revenue') or 0
            revenue_chart.append({
                'date': day,
                'label': day.strftime('%b %d'),
                'orders': item.get('orders') or 0,
                'revenue': revenue,
                'height': max(8, int((revenue / max_chart_revenue) * 100)) if revenue else 8,
            })

        low_stock_products = (
            product_qs.filter(is_active=True, variants__stock__lt=5)
            .annotate(lowest_stock=Min('variants__stock'))
            .distinct()
            .order_by('lowest_stock', 'name_en')[:6]
        )
        latest_orders = orders_qs.order_by('-created_at')[:8]
        recent_activity = (
            LogEntry.objects.select_related('user', 'content_type')
            .order_by('-action_time')[:8]
        )

        quick_actions = [
            {
                'label': 'Add product',
                'icon': 'add_shopping_cart',
                'url': reverse('mohager_admin:products_product_add'),
            },
            {
                'label': 'Review orders',
                'icon': 'receipt_long',
                'url': reverse('mohager_admin:orders_order_changelist'),
            },
            {
                'label': 'Add hero slide',
                'icon': 'view_carousel',
                'url': reverse('mohager_admin:store_heroslide_add'),
            },
            {
                'label': 'Shipping rate',
                'icon': 'local_shipping',
                'url': reverse('mohager_admin:store_storesetting_changelist'),
            },
        ]

        extra_context.update({
            'dashboard_date': today,
            'total_users': total_users,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'pending_orders': pending_orders,
            'products_count': products_count,
            'recent_orders_count': recent_orders_count,
            'recent_revenue': recent_revenue,
            'orders_by_status': orders_by_status,
            'revenue_chart': revenue_chart,
            'latest_orders': latest_orders,
            'low_stock_products': low_stock_products,
            'recent_activity': recent_activity,
            'quick_actions': quick_actions,
            'storefront_url': '/',
        })

        return super().index(request, extra_context)


mohager_admin = MohagerAdminSite(name='mohager_admin')
