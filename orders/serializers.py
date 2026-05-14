from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'variant', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'tracking_no',
            'user',
            'full_name',
            'phone',
            'email',
            'region',
            'address',
            'building',
            'floor',
            'apartment',
            'landmark',
            'status',
            'total_price',
            'created_at',
            'items',
        ]
        read_only_fields = ['tracking_no', 'created_at', 'status']
