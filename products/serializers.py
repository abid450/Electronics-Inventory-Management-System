# apps/products/serializers.py

from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    """Category Serializer"""
    
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent', 'subcategories', 'is_active', 'image', 'icon']
    
    def get_subcategories(self, obj):
        return CategorySerializer(obj.subcategories.filter(is_active=True), many=True).data


class ProductSerializer(serializers.ModelSerializer):
    """Basic Product Serializer (for listing)"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    is_out_of_stock = serializers.BooleanField(read_only=True)
    stock_value = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    profit_margin = serializers.FloatField(read_only=True)
    discount_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'barcode', 'short_description',
            'category', 'category_name',
            'purchase_price', 'selling_price',
            'quantity', 'min_stock_level',
            'is_active', 'is_featured', 'is_new', 'is_best_seller',
            'is_low_stock', 'is_out_of_stock',
            'stock_value', 'profit_margin', 'discount_percentage',
            'main_image', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sku', 'created_at', 'updated_at']


class ProductDetailSerializer(serializers.ModelSerializer):
    """Complete Product Detail Serializer (for details page)"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    is_out_of_stock = serializers.BooleanField(read_only=True)
    stock_value = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    profit_margin = serializers.FloatField(read_only=True)
    discount_percentage = serializers.FloatField(read_only=True)
    
    
    
    class Meta:
        model = Product
        fields = [
            # Basic
            'id', 'name', 'sku', 'barcode',
            'category', 'category_name', 'category_slug',
            
            # ✅ Details (Admin থেকে আসবে)
            'short_description', 'description',
            'specifications', 'highlights',
            
            # Pricing
            'purchase_price', 'selling_price',
            'quantity', 'min_stock_level',
            
            # Status
            'is_active', 'is_featured', 'is_new', 'is_best_seller',
            'is_low_stock', 'is_out_of_stock',
            'stock_value', 'profit_margin', 'discount_percentage',
            
            # Images & Media
            'main_image', 'gallery_images', 'video_url',
            
            # Shipping
            'weight', 'dimensions', 'warranty_period',
            
            # SEO
            'meta_title', 'meta_description', 'meta_keywords',
          
            
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sku', 'created_at', 'updated_at']




class ProductSpecificationSerializer(serializers.Serializer):
    """Product Specifications Serializer"""
    
    key = serializers.CharField()
    value = serializers.CharField()