# apps/customers/serializers.py

from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    total_orders = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'customer_code', 'customer_type', 'status',
            'first_name', 'last_name', 'full_name', 'company_name', 'display_name',
            'email', 'phone', 'alternative_phone',
            'billing_address', 'billing_city', 'billing_state',
            'billing_country', 'billing_pincode',
            'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_pincode', 'is_same_address',
            'credit_limit', 'current_balance', 'total_purchased',
            'discount_percentage', 'loyalty_points', 'loyalty_tier',
            'notes', 'total_orders', 'total_spent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'customer_code', 'created_at', 'updated_at']