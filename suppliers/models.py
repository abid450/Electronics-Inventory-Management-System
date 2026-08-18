# apps/suppliers/models.py

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class Supplier(models.Model):
    """
    Complete Supplier Model
    """
    
    # ============================================
    # Supplier Types
    # ============================================
    SUPPLIER_TYPES = [
        ('MANUFACTURER', 'Manufacturer'),
        ('WHOLESALER', 'Wholesaler'),
        ('DISTRIBUTOR', 'Distributor'),
        ('IMPORTER', 'Importer'),
    ]
    
    # ============================================
    # Supplier Status
    # ============================================
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('BLOCKED', 'Blocked'),
    ]
    
    # ============================================
    # Supplier Rating
    # ============================================
    RATING_CHOICES = [
        (1, '★ Poor'),
        (2, '★★ Fair'),
        (3, '★★★ Good'),
        (4, '★★★★ Very Good'),
        (5, '★★★★★ Excellent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # ============================================
    # Basic Information
    # ============================================
    supplier_code = models.CharField(max_length=50, unique=True, db_index=True)
    supplier_type = models.CharField(max_length=20, choices=SUPPLIER_TYPES, default='WHOLESALER')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    company_name = models.CharField(max_length=200, db_index=True)
    display_name = models.CharField(max_length=200)
    
    # ============================================
    # Contact Person
    # ============================================
    contact_person = models.CharField(max_length=100)
    contact_designation = models.CharField(max_length=100, blank=True)
    
    # ============================================
    # Contact
    # ============================================
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    
    # ============================================
    # Address
    # ============================================
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Bangladesh')
    pincode = models.CharField(max_length=20)
    
    # ============================================
    # Financial
    # ============================================
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_purchased = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # ============================================
    # Payment Terms
    # ============================================
    payment_terms_days = models.IntegerField(default=30, validators=[MinValueValidator(0)])
    bank_name = models.CharField(max_length=200, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    
    # ============================================
    # Performance Metrics
    # ============================================
    rating = models.IntegerField(choices=RATING_CHOICES, default=3)
    average_delivery_days = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    on_time_delivery_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
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
        related_name='suppliers_created'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['supplier_code']),
            models.Index(fields=['company_name']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]
        verbose_name_plural = 'Suppliers'
    
    def __str__(self):
        return self.display_name
    
    def save(self, *args, **kwargs):
        if not self.supplier_code:
            self.supplier_code = self.generate_supplier_code()
        if not self.display_name:
            self.display_name = self.company_name
        super().save(*args, **kwargs)
    
    def generate_supplier_code(self):
        import random, string
        return f"SUP-{''.join(random.choices(string.digits, k=6))}"
    
    @property
    def total_orders(self):
        return self.orders.count()
    
    @property
    def total_supplied(self):
        from django.db.models import Sum
        return self.orders.filter(
            status__in=['DELIVERED', 'SHIPPED']
        ).aggregate(total=Sum('total'))['total'] or 0
    
    def get_full_address(self):
        return f"{self.address}, {self.city}, {self.state} - {self.pincode}"