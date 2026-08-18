# apps/customers/models.py

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class Customer(models.Model):
    """
    Complete Customer Model
    """
    
    # ============================================
    # Customer Types
    # ============================================
    CUSTOMER_TYPES = [
        ('RETAIL', 'Retail Customer'),
        ('WHOLESALE', 'Wholesale Customer'),
        ('CORPORATE', 'Corporate Customer'),
        ('VIP', 'VIP Customer'),
    ]
    
    # ============================================
    # Customer Status
    # ============================================
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('BLOCKED', 'Blocked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # ============================================
    # Basic Information
    # ============================================
    customer_code = models.CharField(max_length=50, unique=True, db_index=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default='RETAIL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    display_name = models.CharField(max_length=200)
    
    # ============================================
    # Contact
    # ============================================
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True)
    
    # ============================================
    # Address
    # ============================================
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=100)
    billing_country = models.CharField(max_length=100, default='Bangladesh')
    billing_pincode = models.CharField(max_length=20)
    
    shipping_address = models.TextField(blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_pincode = models.CharField(max_length=20, blank=True)
    
    is_same_address = models.BooleanField(default=True)
    
    # ============================================
    # Financial
    # ============================================
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_purchased = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # ============================================
    # Discount
    # ============================================
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # ============================================
    # Loyalty
    # ============================================
    loyalty_points = models.IntegerField(default=0)
    loyalty_tier = models.CharField(max_length=50, default='Bronze')
    
    # ============================================
    # Notes
    # ============================================
    notes = models.TextField(blank=True)
    
    # ============================================
    # Timestamps
    # ============================================
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='customers_created'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_code']),
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['status']),
        ]
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return self.display_name or f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        if not self.customer_code:
            self.customer_code = self.generate_customer_code()
        if not self.display_name:
            self.display_name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)
    
    def generate_customer_code(self):
        import random, string
        return f"CUS-{''.join(random.choices(string.digits, k=6))}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def total_orders(self):
        return self.orders.count()
    
    @property
    def total_spent(self):
        from django.db.models import Sum
        return self.orders.filter(
            status__in=['DELIVERED', 'SHIPPED']
        ).aggregate(total=Sum('total'))['total'] or 0
    
    def get_full_address(self):
        return f"{self.billing_address}, {self.billing_city}, {self.billing_state} - {self.billing_pincode}"