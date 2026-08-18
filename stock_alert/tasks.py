# apps/stock/tasks.py

from celery import shared_task
from django.db.models import F, Sum
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from products.models import Product
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# ============================================================
# 1. CHECK LOW STOCK (শুধু চেক করে, ইমেইল পাঠায় না)
# ============================================================

@shared_task(name='stock_alert.tasks.check_low_stock')
def check_low_stock():
    """
    Check low stock products - শুধু ডাটা সংগ্রহ করে
    """
    low_stock_products = Product.objects.filter(
        quantity__lte=F('min_stock_level'),
        is_active=True
    )
    
    out_of_stock_products = Product.objects.filter(
        quantity=0,
        is_active=True
    )
    
    low_count = low_stock_products.count()
    out_count = out_of_stock_products.count()
    
    return {
        'status': 'success',
        'low_stock_count': low_count,
        'out_of_stock_count': out_count,
        'low_stock_items': list(low_stock_products.values('id', 'name', 'sku', 'quantity', 'min_stock_level')),
        'out_of_stock_items': list(out_of_stock_products.values('id', 'name', 'sku', 'quantity')),
        'timestamp': str(timezone.now())
    }


# ============================================================
# 2. SEND LOW STOCK EMAIL (শুধু ইমেইল পাঠায়)
# ============================================================

@shared_task(name='stock_alert.tasks.send_low_stock_email')
def send_low_stock_email(low_count=None, out_count=None, low_stock_items=None, out_of_stock_items=None):
    """
    Send low stock alert email - শুধু ইমেইল পাঠায়
    """
    
    # যদি ডাটা না আসে, নিজে সংগ্রহ করো
    if low_stock_items is None:
        result = check_low_stock()
        low_count = result['low_stock_count']
        out_count = result['out_of_stock_count']
        low_stock_items = result['low_stock_items']
        out_of_stock_items = result['out_of_stock_items']
    
    # যদি Low Stock না থাকে, ইমেইল পাঠাবেন না
    if low_count == 0 and out_count == 0:
        return {'status': 'success', 'message': 'No low stock items found'}
    
    # Admin emails
    admin_emails = getattr(settings, 'ADMIN_EMAILS', [])
    if not admin_emails:
        admin_emails = [settings.DEFAULT_FROM_EMAIL]
    if isinstance(admin_emails, str):
        admin_emails = [admin_emails]
    
    # Context
    context = {
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
        'low_count': low_count,
        'out_count': out_count,
        'total_alerts': low_count + out_count,
        'site_name': getattr(settings, 'SITE_NAME', 'Inventory System'),
        'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        'current_time': timezone.now(),
        'year': timezone.now().year,
    }
    
    # Email send
    html_message = render_to_string('low_stock_alert.html', context)
    plain_message = strip_tags(html_message)
    
    subject = f"🚨 Low Stock Alert - {low_count + out_count} items need attention"
    
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=admin_emails,
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        
        return {
            'status': 'success',
            'message': f'Low stock alert sent to {len(admin_emails)} admins'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


# ============================================================
# 3. CHECK AND NOTIFY (একসাথে চেক + ইমেইল)
# ============================================================

@shared_task(name='stock_alert.tasks.check_and_notify_low_stock')
def check_and_notify_low_stock():
    """
    Combined task: check low stock and send notification - এখান থেকে ইমেইল পাঠায়
    """
    result = check_low_stock()
    
    low_count = result['low_stock_count']
    out_count = result['out_of_stock_count']
    
    if low_count > 0 or out_count > 0:
        send_low_stock_email.delay(
            low_count,
            out_count,
            result['low_stock_items'],
            result['out_of_stock_items']
        )
    
    return {
        'status': 'success',
        'low_stock_count': low_count,
        'out_of_stock_count': out_count,
        'timestamp': str(timezone.now())
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_confirmation_email(self, transaction_id):
    """
    Send payment confirmation email to customer
    """
    try:
        from checkout.models import PaymentTransaction
        
        # Get transaction from database
        transaction = PaymentTransaction.objects.get(id=transaction_id)
        
        # Prepare email context
        context = {
            'transaction': transaction,
            'tran_id': transaction.tran_id,
            'amount': transaction.amount,
            'payment_method': transaction.payment_method or 'N/A',
            'paid_at': transaction.paid_at or timezone.now(),
            'customer_name': transaction.customer_name,
            'customer_email': transaction.customer_email,
            'customer_phone': transaction.customer_phone,
            'customer_address': transaction.customer_address or 'N/A',
            'customer_city': transaction.customer_city or 'N/A',
            'year': timezone.now().year
        }
        
        # Render HTML email template
        html_content = render_to_string('payment_confirmation.html', context)
        text_content = strip_tags(html_content)
        
        subject = f'Payment Confirmation - {transaction.tran_id}'
        
        # Create email with HTML and plain text versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[transaction.customer_email],
            
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        logger.info(f"Payment confirmation email sent to {transaction.customer_email}")
        return {'status': 'success', 'email': transaction.customer_email}
        
    except Exception as e:
        logger.error(f"Failed to send payment confirmation email: {str(e)}")
        raise self.retry(exc=e, countdown=60)
    


@shared_task
def send_pending_reminder():
    """
    Send reminder for pending transactions (optional)
    """
    from checkout.models import PaymentTransaction
    
    pending_transactions = PaymentTransaction.objects.filter(
        status='pending',
        created_at__gte=timezone.now() - timedelta(hours=24)
    )
    
    sent_count = 1
    for transaction in pending_transactions:
        # Send reminder email
        subject = f'Payment Reminder - {transaction.tran_id}'
        message = f"""
        Dear {transaction.customer_name},
        
        Your payment with Transaction ID: {transaction.tran_id} is still pending.
        Amount: ৳{transaction.amount}
        Date: {transaction.created_at}
        
        If you have already made the payment, please ignore this message.
        
        Thank you,
        Your Team
        """
        
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [transaction.customer_email])
        sent_count += 1
    
    return {'status': 'success', 'sent_count': sent_count}


