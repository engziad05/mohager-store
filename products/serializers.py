from rest_framework import serializers
from store.models import Product, ProductImage, ProductVariant, Category


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'size', 'stock', 'stock_quantity']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name_en', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name_en',
            'name_ar',
            'description_en',
            'description_ar',
            'base_price',
            'color_en',
            'color_ar',
            'color_code',
            'image',
            'category',
            'category_name',
            'is_active',
            'created_at',
            'images',
            'variants',
        ]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name_en', 'name_ar', 'slug']
