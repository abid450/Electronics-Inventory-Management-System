# apps/orders/serializers.py

from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Order Item Serializer"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'total_price',
            'created_at'
        ]
        read_only_fields = ['id', 'total_price', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    """Complete Order Serializer"""
    
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=20)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status',
            'customer_name', 'customer_email', 'customer_phone',
            'customer_address', 'customer_city',
            'subtotal', 'tax_amount', 'shipping_cost', 'total',
            'payment_method', 'payment_status', 'transaction_id',
            'items', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'created_at', 'updated_at',
            'payment_status', 'status'
        ]


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating order from checkout"""
    
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=20)
    customer_address = serializers.CharField(required=False, allow_blank=True)
    customer_city = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.CharField(max_length=20, default='SSLCOMMERZ')
    notes = serializers.CharField(required=False, allow_blank=True)
    
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )
    
    def validate_items(self, value):
        for item in value:
            if 'product_id' not in item:
                raise serializers.ValidationError("Each item must have product_id")
            if 'quantity' not in item or item['quantity'] < 1:
                raise serializers.ValidationError("Each item must have quantity >= 1")
        return value


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Update Order Status"""
    
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True)


class OrderListSerializer(serializers.ModelSerializer):
    """Simplified Order List Serializer"""
    
    total_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name',
            'total', 'status', 'payment_status',
            'total_items', 'created_at'
        ]
    
    def get_total_items(self, obj):
        return obj.items.count()