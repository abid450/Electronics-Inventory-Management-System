from django.db import models

# Create your models here.
# apps/cart/models.py

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from products.models import Product

User = get_user_model()


class Cart(models.Model):
    """
    Shopping Cart Model
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cart_cart'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]
    
    def __str__(self):
        if self.user:
            return f"Cart - {self.user.email}"
        return f"Cart - {self.session_key}"
    
    def get_total_items(self):
        """Get total number of items in cart"""
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    def get_total_price(self):
        """Get total price of all items"""
        total = 0
        for item in self.items.all():
            total += item.get_subtotal()
        return total
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()
    
    def get_items_data(self):
        """Get cart items as list of dicts"""
        return [
            {
                'product_id': str(item.product.id),
                'name': item.product.name,
                'sku': item.product.sku,
                'price': float(item.product.selling_price),
                'quantity': item.quantity,
                'subtotal': float(item.get_subtotal()),
                'image': str(item.product.main_image) if item.product.main_image else None,
            }
            for item in self.items.select_related('product').all()
        ]


class CartItem(models.Model):
    """
    Cart Item Model
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cart_cartitem'
        unique_together = ['cart', 'product']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def get_subtotal(self):
        """Calculate subtotal for this item"""
        return self.product.selling_price * self.quantity