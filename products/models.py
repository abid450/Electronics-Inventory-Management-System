# apps/products/models.py

import uuid
import random
import string
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify


class Category(models.Model):
    """Product Category"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategories'
    )
    is_active = models.BooleanField(default=True)
    
    # Category Image
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Complete Product Model with Details Fields"""
    
    # ============================================
    # Basic Information
    # ============================================
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True)
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    barcode = models.CharField(max_length=50, blank=True, null=True)
    
    # ============================================
    # Category
    # ============================================
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )
    
    # ============================================
    # Pricing
    # ============================================
    purchase_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00
    )
    selling_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00
    )
    
    # ============================================
    # Stock
    # ============================================
    quantity = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=5)
    
    # ============================================
    # ✅ DETAILS FIELDS (Admin থেকে যোগ করা হবে)
    # ============================================
    
    # Description
    short_description = models.CharField(
        max_length=300, 
        blank=True, 
        help_text="Short description for product listing"
    )
    description = models.TextField(
        blank=True, 
        help_text="Full product description with details"
    )
    
    # Product Specifications (JSON format)
    specifications = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Product specifications in JSON format. e.g., {'Brand': 'Apple', 'Model': 'iPhone 15', 'Color': 'Black'}"
    )
    
    # Highlights / Features
    highlights = models.JSONField(
        default=list, 
        blank=True,
        help_text="Key features/highlights of the product. e.g., ['Feature 1', 'Feature 2']"
    )
    
    # Images
    main_image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    # Gallery Images (Multiple)
    gallery_images = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of additional product images"
    )
    
    # Video URL (YouTube/Vimeo)
    video_url = models.URLField(
        blank=True, 
        null=True,
        help_text="Product video URL (YouTube/Vimeo)"
    )
    
    # SEO Fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)
    
    # ============================================
    # Status
    # ============================================
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    
    # ============================================
    # Shipping & Warranty
    # ============================================
    weight = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00,
        help_text="Weight in kg"
    )
    dimensions = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Product dimensions (L x W x H)"
    )
    warranty_period = models.IntegerField(
        default=0, 
        help_text="Warranty period in months"
    )
    
    # ============================================
    # Timestamps
    # ============================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self.generate_sku()
        super().save(*args, **kwargs)
    
    def generate_sku(self):
        prefix = ''.join([w[0].upper() for w in self.name.split()[:2]])
        if not prefix:
            prefix = 'PRD'
        code = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}-{code}"
    
    # ============================================
    # Properties
    # ============================================
    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock_level
    
    @property
    def is_out_of_stock(self):
        return self.quantity <= 0
    
    @property
    def stock_value(self):
        return self.quantity * self.purchase_price
    
    @property
    def profit_margin(self):
        if self.purchase_price > 0:
            return round(
                ((self.selling_price - self.purchase_price) / self.purchase_price) * 100,
                2
            )
        return 0
    
    @property
    def discount_percentage(self):
        if self.purchase_price > 0 and self.selling_price < self.purchase_price:
            return round(
                ((self.purchase_price - self.selling_price) / self.purchase_price) * 100,
                2
            )
        return 0