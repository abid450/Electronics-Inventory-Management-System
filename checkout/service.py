# Payment/services.py
import uuid
import logging
import time
import random
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from sslcommerz_lib import SSLCOMMERZ
from .models import PaymentTransaction, PaymentLog

logger = logging.getLogger(__name__)


class SSLCommerzPaymentService:
    """
    Professional SSLCommerz Payment Gateway Service
    """
    
    def __init__(self):
        self.settings = {
            'store_id': settings.SSLCOMMERZ_STORE_ID,
            'store_pass': settings.SSLCOMMERZ_STORE_PASSWORD,
            'issandbox': settings.SSLCOMMERZ_SANDBOX
        }
        self.sslcz = SSLCOMMERZ(self.settings)
    
    def initiate_payment(self, payment_data):
        """
        Initialize payment session with SSLCommerz
        """
        try:
            # Generate unique transaction ID
            tran_id = self.generate_transaction_id()
            
            # Prepare post body for SSLCommerz
            post_body = {
                'total_amount': str(payment_data['amount']),
                'currency': payment_data.get('currency', 'BDT'),
                'tran_id': tran_id,
                'success_url': settings.PAYMENT_SUCCESS_URL,
                'fail_url': settings.PAYMENT_FAIL_URL,
                'cancel_url': settings.PAYMENT_CANCEL_URL,
                'ipn_url': settings.PAYMENT_IPN_URL,
                'emi_option': 0,
                'cus_name': payment_data['customer_name'],
                'cus_email': payment_data['customer_email'],
                'cus_phone': payment_data['customer_phone'],
                'cus_add1': payment_data.get('customer_address'),
                'cus_city': payment_data.get('customer_city'),
                'cus_country': payment_data.get('customer_country'),
                'shipping_method': 'NO',
                'multi_card_name': '',
                'num_of_item': payment_data.get('num_of_item', 1),
                'product_name': payment_data.get('product_name', 'Payment'),
                'product_category': payment_data.get('product_category', 'General'),
                'product_profile': 'general',
            }
            
            # Create transaction record
            transaction = PaymentTransaction.objects.create(
                tran_id=tran_id,
                amount=payment_data['amount'],
                currency=post_body['currency'],
                customer_name=payment_data['customer_name'],
                customer_email=payment_data['customer_email'],
                customer_phone=payment_data['customer_phone'],
                customer_address=payment_data.get('customer_address'),
                customer_city=payment_data.get('customer_city'),
                order_id=payment_data.get('order_id', None)
            )
            
            # Log initiation
            PaymentLog.objects.create(
                transaction=transaction,
                action='initiate',
                request_data=post_body
            )
            
            # Call SSLCommerz API
            response = self.sslcz.createSession(post_body)
            
            if response and response.get('status') == 'SUCCESS':
                # Update transaction with session key
                transaction.sessionkey = response.get('sessionkey')
                transaction.status = 'pending'
                transaction.save()
                
                # Cache transaction for quick access
                cache.set(f'payment_{tran_id}', transaction.id, 3600)
                
                return {
                    'success': True,
                    'gateway_url': response['GatewayPageURL'],
                    'tran_id': tran_id,
                    'transaction': transaction
                }
            else:
                transaction.mark_as_failed(response.get('failedreason', 'Unknown error'))
                return {
                    'success': False,
                    'error': response.get('failedreason', 'Payment initiation failed'),
                    'tran_id': tran_id
                }
                
        except Exception as e:
            logger.error(f"Payment initiation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_payment(self, payment_data):
        """
        Validate payment after successful transaction
        """
        try:
            # Validate hash with SSLCommerz
            if not self.sslcz.hash_validate_ipn(payment_data):
                logger.warning(f"Hash validation failed for transaction: {payment_data.get('tran_id')}")
                return {'success': False, 'error': 'Hash validation failed'}
            
            # Get transaction
            tran_id = payment_data.get('tran_id')
            try:
                transaction = PaymentTransaction.objects.get(tran_id=tran_id)
            except PaymentTransaction.DoesNotExist:
                return {'success': False, 'error': 'Transaction not found'}
            
            # Validate with SSLCommerz API
            validation_response = self.sslcz.validationTransactionOrder(payment_data.get('val_id'))
            
            if validation_response and validation_response.get('status') == 'VALID':
                transaction.mark_as_completed(validation_response)
                transaction.ipn_response = payment_data
                transaction.save()
                
                PaymentLog.objects.create(
                    transaction=transaction,
                    action='ipn_success',
                    response_data=validation_response
                )
                
                # Clear cache
                cache.delete(f'payment_{tran_id}')
                
                return {
                    'success': True,
                    'transaction': transaction,
                    'validation_data': validation_response
                }
            else:
                transaction.mark_as_failed('Validation failed')
                return {
                    'success': False,
                    'error': 'Payment validation failed',
                    'transaction': transaction
                }
                
        except Exception as e:
            logger.error(f"Payment validation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def retry_payment(self, transaction_id):
        """
        Retry failed payment
        """
        try:
            transaction = PaymentTransaction.objects.get(id=transaction_id)
            
            if not transaction.can_retry():
                return {
                    'success': False,
                    'error': 'Maximum retry attempts reached or transaction not eligible for retry'
                }
            
            transaction.increment_retry()
            
            # Prepare retry data
            retry_data = {
                'amount': transaction.amount,
                'currency': transaction.currency,
                'customer_name': transaction.customer_name,
                'customer_email': transaction.customer_email,
                'customer_phone': transaction.customer_phone,
                'order_id': transaction.order_id
            }
            
            PaymentLog.objects.create(
                transaction=transaction,
                action='retry',
                request_data={'retry_count': transaction.retry_count}
            )
            
            # Initiate new payment
            return self.initiate_payment(retry_data)
            
        except PaymentTransaction.DoesNotExist:
            return {'success': False, 'error': 'Transaction not found'}
    
    def get_transaction_status(self, tran_id):
        """
        Get transaction status from SSLCommerz
        """
        try:
            # Check local database first
            try:
                transaction = PaymentTransaction.objects.get(tran_id=tran_id)
                if transaction.status in ['completed', 'failed', 'cancelled']:
                    return {
                        'success': True,
                        'status': transaction.status,
                        'transaction': transaction
                    }
            except PaymentTransaction.DoesNotExist:
                pass
            
            # Query SSLCommerz API
            response = self.sslcz.transaction_query_by_tran_id({'tran_id': tran_id})
            
            if response:
                return {
                    'success': True,
                    'status': response.get('status', 'unknown'),
                    'data': response
                }
            
            return {'success': False, 'error': 'Transaction not found'}
            
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def initiate_refund(self, tran_id, amount=None, remarks=None):
        """
        Initiate refund for a transaction
        """
        try:
            transaction = PaymentTransaction.objects.get(tran_id=tran_id)
            
            if transaction.status != 'completed':
                return {'success': False, 'error': 'Only completed transactions can be refunded'}
            
            refund_data = {
                'refund_amount': float(amount) if amount else float(transaction.amount),
                'refund_remarks': remarks or 'Customer requested refund',
                'bank_tran_id': transaction.bank_tran_id,
                'bank_name' : transaction.bank_name,
                'refe_id': transaction.tran_id,
            }
            
            response = self.sslcz.initiateRefund(refund_data)
            
            if response and response.get('status') == 'success':
                transaction.status = 'refunded'
                transaction.save()
                
                PaymentLog.objects.create(
                    transaction=transaction,
                    action='refund',
                    response_data=response
                )
                
                return {'success': True, 'data': response}
            else:
                return {'success': False, 'error': response.get('failedreason', 'Refund failed')}
                
        except Exception as e:
            logger.error(f"Refund failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def generate_transaction_id():
        """
        Generate unique transaction ID
        """
        import time
        import random
        timestamp = int(time.time())
        random_num = random.randint(1000, 9999)
        return f"TXN_{timestamp}_{random_num}"