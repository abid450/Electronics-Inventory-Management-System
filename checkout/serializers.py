# apps/payment/serializers.py

from rest_framework import serializers
from .models import PaymentTransaction, PaymentLog


class CheckoutSerializer(serializers.Serializer):
    """Complete Checkout Serializer with Cart Items"""
    
    # Customer Info
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=20)
    customer_address = serializers.CharField(required=False, allow_blank=True)
    customer_city = serializers.CharField(required=False, allow_blank=True)
    
    # Payment
    payment_method = serializers.CharField(max_length=20, default='SSLCOMMERZ')
    
    # Cart Items
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )
    
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_items(self, value):
        for item in value:
            if 'product_id' not in item:
                raise serializers.ValidationError("Each item must have product_id")
            if 'quantity' not in item or item['quantity'] < 1:
                raise serializers.ValidationError("Each item must have quantity >= 1")
        return value


class PaymentInitiateSerializer(serializers.Serializer):
    """Payment Initiate Serializer (for direct payment)"""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=1)
    currency = serializers.CharField(default='BDT', max_length=10)
    customer_name = serializers.CharField(max_length=100)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=20)
    customer_address = serializers.CharField(required=False, allow_blank=True)
    customer_city = serializers.CharField(required=False, allow_blank=True)
    order_id = serializers.CharField(required=False, allow_blank=True)
    product_name = serializers.CharField(default='Payment', max_length=200)
    num_of_item = serializers.IntegerField(default=1, min_value=1)


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = '__all__'
        read_only_fields = ['id', 'tran_id', 'sessionkey', 'val_id', 'created_at', 'updated_at', 'paid_at']


class PaymentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLog
        fields = '__all__'