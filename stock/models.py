from django.db import models

# Create your models here.
# apps/stock/models.py

import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Warehouse(models.Model):
    """Warehouse/Location Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, db_index=True)
    code = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Address
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Bangladesh')
    pincode = models.CharField(max_length=20)
    
    # Contact
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    manager = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Warehouses'
    
    def __str__(self):
        return self.name


class Stock(models.Model):
    """Current Stock at Warehouse"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='stocks'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='stocks'
    )
    
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reserved_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    available_quantity = models.IntegerField(default=0)
    
    min_stock_level = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    max_stock_level = models.IntegerField(default=100, validators=[MinValueValidator(0)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'warehouse']
        verbose_name_plural = 'Stocks'
        indexes = [
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['quantity']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.warehouse.name}: {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.available_quantity = self.quantity - self.reserved_quantity
        super().save(*args, **kwargs)


class StockTransaction(models.Model):
    """Stock Movement History"""
    
    TRANSACTION_TYPES = [
        ('IN', 'Purchase In'),
        ('OUT', 'Sale Out'),
        ('ADJUST', 'Adjustment'),
        ('RETURN', 'Return In'),
        ('TRANSFER', 'Transfer'),
        ('WASTE', 'Wastage'),
        ('COUNT', 'Stock Count'),
        ('CANCEL', 'Order Cancel'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True
    )
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_transactions'
    )
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    
    reason = models.CharField(max_length=200, blank=True)
    reference = models.CharField(max_length=100, blank=True, db_index=True)  # Order/Invoice/PO number
    
    note = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['reference']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.transaction_type}: {self.quantity}"