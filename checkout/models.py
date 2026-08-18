from django.db import models
import uuid
from django.utils import timezone
# Create your models here.


class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    
    ]

    PAYMENT_METHODS = [
        ('card', 'Credit/Debit Card'),
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('rocket', 'Rocket'),
        ('bank', 'Bank Transfer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tran_id = models.CharField(max_length=100, unique=True, db_index=True)
    sessionkey = models.CharField(max_length=200, blank=True, null=True)
    val_id = models.CharField(max_length=200, blank=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='BDT')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True, null=True)

    # Customer Information
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    customer_address = models.TextField(null=True, blank=True)
    customer_city = models.CharField(max_length=50, null=True, blank=True)
    customer_country = models.CharField(max_length=50)
    
    # Order Information (optional - link to your order model)
    order_id = models.CharField(max_length=100, blank=True, null=True)
    order_number = models.CharField(max_length=50, blank=True, null=True)

    # Card Information (if card payment)
    card_type = models.CharField(max_length=50, blank=True, null=True)
    card_number = models.CharField(max_length=20, blank=True, null=True)
    card_issuer = models.CharField(max_length=100, blank=True, null=True)
    
    # Bank Information
    bank_tran_id = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)


    # Error Handling
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    # IPN Information
    ipn_response = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'payment_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tran_id']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.tran_id} - {self.amount} {self.currency} - {self.status}"
    
    def mark_as_completed(self, payment_data=None):
        """Mark transaction as completed"""
        self.status = 'completed'
        self.paid_at = timezone.now()
        if payment_data:
            self.payment_method = payment_data.get('card_type', 'card')
            self.card_type = payment_data.get('card_type')
            self.card_number = payment_data.get('card_number')
            self.card_issuer = payment_data.get('card_issuer')
            self.bank_tran_id = payment_data.get('bank_tran_id')
        self.save()
    
    def mark_as_failed(self, error_message=None):
        """Mark transaction as failed"""
        self.status = 'failed'
        if error_message:
            self.error_message = error_message
        self.save()
    
    def mark_as_cancelled(self):
        """Mark transaction as cancelled"""
        self.status = 'cancelled'
        self.save()
    
    def can_retry(self):
        """Check if transaction can be retried"""
        return self.status == 'failed' and self.retry_count < self.max_retries
    
    def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1
        self.save()
        return self.retry_count



class PaymentLog(models.Model):
    """
    Payment Log for debugging and monitoring
    """
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=50)  # 'initiate', 'success', 'failed', 'ipn', 'retry'
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction.tran_id} - {self.action} - {self.created_at}"


    