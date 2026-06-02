from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductVariant, ProductColor


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'size', 'stock']


class ProductColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductColor
        fields = ['id', 'name_ar', 'name_en', 'color_code', 'main_image', 'price', 'is_default']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    colors = ProductColorSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name_en', read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name_en',
            'name_ar',
            'description_en',
            'description_ar',
            'base_price',
            'compare_at_price',
            'has_discount',
            'discount_percent',
            'image',
            'category',
            'category_name',
            'is_active',
            'created_at',
            'images',
            'variants',
            'colors',
        ]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name_en', 'name_ar', 'slug']
