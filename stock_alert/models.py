from django.db import models

# Create your models here.
# apps/stock/models.py

import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone  

User = get_user_model()


class StockAlert(models.Model):
    """
    Stock Alert Model for tracking low stock notifications
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    current_quantity = models.IntegerField()
    min_level = models.IntegerField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stock Alerts'
    
    def __str__(self):
        return f"Alert: {self.product.name} - {self.current_quantity}/{self.min_level}"
    
    def resolve(self):
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()