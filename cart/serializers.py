# apps/cart/serializers.py

from rest_framework import serializers
from .models import Cart, CartItem
from products.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    """Cart Item Serializer"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_price = serializers.DecimalField(source='product.selling_price', read_only=True, max_digits=12, decimal_places=2)
    subtotal = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'product_price', 'quantity', 'subtotal', 'image',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_subtotal(self, obj):
        return obj.get_subtotal()
    
    # Image Url ------------------------------
    def get_image(self, obj):
        if obj.product and obj.product.main_image:
            try:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.product.main_image.url)
                return obj.product.main_image.url

            except Exception as e:
                print(f"Image URL error: {e}")
                return None
        return None



class AddToCartSerializer(serializers.Serializer):
    """Add to Cart Request Serializer"""
    
    product_id = serializers.UUIDField(required=True)
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateCartSerializer(serializers.Serializer):
    """Update Cart Request Serializer"""
    
    product_id = serializers.UUIDField(required=True)
    quantity = serializers.IntegerField(min_value=0)


class RemoveFromCartSerializer(serializers.Serializer):
    """Remove from Cart Request Serializer"""
    
    product_id = serializers.UUIDField(required=True)


class CartSerializer(serializers.ModelSerializer):
    """Complete Cart Serializer"""
    
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_items', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    
    def get_total_price(self, obj):
        return obj.get_total_price()