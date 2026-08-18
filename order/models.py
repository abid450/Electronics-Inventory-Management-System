from django.db import models

# Create your models here.
# apps/orders/models.py

import uuid
import random
import string
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Order(models.Model):
    """
    Complete Order Model
    """
    
    # ============================================
    # Status Choices
    # ============================================
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed'),
    ]
    
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('SSLCOMMERZ', 'SSLCommerz'),
        ('BKASH', 'bKash'),
        ('NAGAD', 'Nagad'),
        ('COD', 'Cash on Delivery'),
        ('CARD', 'Credit/Debit Card'),
    ]
    
    # ============================================
    # Basic Fields
    # ============================================
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # ============================================
    # Customer Information
    # ============================================
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    customer_address = models.TextField(blank=True)
    customer_city = models.CharField(max_length=100, blank=True)
    
    # ============================================
    # Financial
    # ============================================
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # ============================================
    # Payment
    # ============================================
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='SSLCOMMERZ')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    ssl_session_id = models.CharField(max_length=100, blank=True, null=True)
    
    # ============================================
    # SSLCommerz Specific
    # ============================================
    ssl_status = models.CharField(max_length=50, blank=True, null=True)
    ssl_validation_id = models.CharField(max_length=100, blank=True, null=True)
    
    # ============================================
    # Notes
    # ============================================
    notes = models.TextField(blank=True)
    
    # ============================================
    # Timestamps
    # ============================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'order_order'
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['customer_email']),
        ]
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        code = ''.join(random.choices(string.digits, k=8))
        return f"ORD-{code}"
    
    def mark_as_paid(self, transaction_id, ssl_session_id=None):
        self.payment_status = 'PAID'
        self.transaction_id = transaction_id
        self.ssl_session_id = ssl_session_id
        self.status = 'PROCESSING'
        self.save()


class OrderItem(models.Model):
    """
    Order Items
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='order_items')
    
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_orderitem'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)