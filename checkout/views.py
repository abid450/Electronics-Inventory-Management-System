# apps/payment/views.py

from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from .models import PaymentTransaction
from .serializers import CheckoutSerializer, PaymentInitiateSerializer, PaymentTransactionSerializer
from .service import SSLCommerzPaymentService
from order.models import *
from order.serializers import *
from stock_alert.tasks import send_payment_confirmation_email
import logging
import json
from decimal import Decimal


logger = logging.getLogger(__name__)



# ============================================
# ✅ CART CLEAR HELPER FUNCTION
# ============================================

def clear_user_cart(request):
    """
    Clear cart from both session and database
    """
    try:
        # 1. Clear session cart
        if request.session.get('cart'):
            request.session['cart'] = {}
            request.session.modified = True
            logger.info("✅ Session cart cleared")
        
        # 2. Clear database cart for authenticated user
        if request.user and request.user.is_authenticated:
            try:
                from cart.models import Cart
                cart = Cart.objects.filter(user=request.user).first()
                if cart:
                    cart.clear()
                    cart.delete()
                    logger.info(f"✅ Database cart cleared for user: {request.user.email}")
            except ImportError:
                pass  # cart app not installed
        
        # 3. Clear session cart ID
        if request.session.get('cart_session_id'):
            try:
                from cart.models import Cart
                cart = Cart.objects.get(id=request.session['cart_session_id'])
                cart.clear()
                cart.delete()
                logger.info(f"✅ Session cart cleared: {request.session['cart_session_id']}")
            except:
                pass
            del request.session['cart_session_id']
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error clearing cart: {str(e)}")
        return False



@csrf_exempt
def checkout_initiate(request):
    """
    Complete Checkout API with Cart Items
    POST: /checkout/api/initiate/
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        serializer = CheckoutSerializer(data=data)
        
        if not serializer.is_valid():
            return JsonResponse({
                'status': 'error',
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=400)
        
        validated_data = serializer.validated_data
        
        # ============================================
        # Step 1: Calculate Total from Cart Items
        # ============================================
        subtotal = Decimal('0.00')
        items_data = []
        
        for item in validated_data['items']:
            from products.models import Product
            product = get_object_or_404(Product, id=item['product_id'])
            
            # Check stock
            if product.quantity < item['quantity']:
                return JsonResponse({
                    'status': 'error',
                    'message': f"Insufficient stock for {product.name}",
                    'errors': {'items': f"{product.name} has only {product.quantity} in stock"}
                }, status=400)
            
            unit_price = Decimal(str(item.get('unit_price', product.selling_price)))
            quantity = int(item['quantity'])
            total_price = unit_price * item['quantity']
            subtotal += total_price
            
            items_data.append({
                'product': product,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price,
            })
        
        tax_amount = subtotal * Decimal('0.05')
        shipping_cost = Decimal('100.00')
        total = subtotal + tax_amount + shipping_cost
        
        # ============================================
        # Step 2: Create Order
        # ============================================
        from order.models import Order, OrderItem as OrderItemModel
        
        order = Order.objects.create(
            customer_name=validated_data['customer_name'],
            customer_email=validated_data['customer_email'],
            customer_phone=validated_data['customer_phone'],
            customer_address=validated_data.get('customer_address', ''),
            customer_city=validated_data.get('customer_city', ''),
            payment_method=validated_data['payment_method'],
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            total=total,
            notes=validated_data.get('notes', '')
        )
        
        for item_data in items_data:
            OrderItemModel.objects.create(
                order=order,
                product=item_data['product'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price']
            )
        
        # ============================================
        # Step 3: Initiate SSLCommerz Payment
        # ============================================
        service = SSLCommerzPaymentService()
        
        payment_result = service.initiate_payment({
            'amount': float(total),
            'currency': 'BDT',
            'customer_name': validated_data['customer_name'],
            'customer_email': validated_data['customer_email'],
            'customer_phone': validated_data['customer_phone'],
            'customer_address': validated_data.get('customer_address', ''),
            'customer_city': validated_data.get('customer_city', ''),
            'customer_country': 'Bangladesh',
            'order_id': str(order.id),
            'product_name': 'Order Payment',
            'num_of_item': len(items_data)
        })
        
        if payment_result.get('success'):
            clear_user_cart(request)

            return JsonResponse({
                'status': 'success',
                'message': 'Payment initiated successfully',
                'data': {
                    'payment_url': payment_result['gateway_url'],
                    'tran_id': payment_result['tran_id'],
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': payment_result.get('error', 'Payment initiation failed')
            }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Checkout error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



# Payment/views.py - সম্পূর্ণ আপডেটেড

@method_decorator(csrf_exempt, name='dispatch')
class PaymentSuccessView(View):
    """
    Handle successful payment redirect with full customer info
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.payment_service = SSLCommerzPaymentService()
    
    def get(self, request):
        """Handle GET request from SSLCommerz"""
        payment_data = request.GET.dict()
        return self._process_payment(request, payment_data)
    
    def post(self, request):
        """Handle POST request from SSLCommerz"""
        payment_data = request.POST.dict()
        return self._process_payment(request, payment_data)
    
    def _process_payment(self, request, payment_data):
        """Process payment data and show success page"""
        tran_id = payment_data.get('tran_id')
        
        if not tran_id:
            return render(request, 'failed.html', {
                'error': 'No transaction ID found',
                'message': 'Transaction ID missing from payment response'
            })


        clear_user_cart(request)
        # Try to get transaction from database
        try:
            transaction = PaymentTransaction.objects.get(tran_id=tran_id)
        except PaymentTransaction.DoesNotExist:
            transaction = None
        
        # If transaction exists and is completed
        if transaction and transaction.status == 'completed':
            send_payment_confirmation_email.delay(str(transaction.id))

            context = {
                'transaction': transaction,
                'tran_id': transaction.tran_id,
                'amount': transaction.amount,
                'payment_method': transaction.payment_method or 'N/A',
                'paid_at': transaction.paid_at,
                'customer_name': transaction.customer_name or 'N/A',
                'customer_email': transaction.customer_email or 'N/A',
                'customer_phone': transaction.customer_phone or 'N/A',
                'customer_address': transaction.customer_address or 'N/A',
                'customer_city': transaction.customer_city or 'N/A',
                'success': True,
                'message': 'Payment successful!'
            }
            return render(request, 'success.html', context)
        
        # Validate payment with SSLCommerz
        result = self.payment_service.validate_payment(payment_data)
        
        if result.get('success'):
            transaction = result.get('transaction')
            send_payment_confirmation_email.delay(str(transaction.id))

            context = {
                'transaction': transaction,
                'tran_id': transaction.tran_id,
                'amount': transaction.amount,
                'payment_method': transaction.payment_method or 'N/A',
                'paid_at': transaction.paid_at,
                'customer_name': transaction.customer_name or 'N/A',
                'customer_email': transaction.customer_email or 'N/A',
                'customer_phone': transaction.customer_phone or 'N/A',
                'customer_address': transaction.customer_address or 'N/A',
                'customer_city': transaction.customer_city or 'N/A',
                'success': True,
                'message': 'Payment successful!'
            }
            return render(request, 'success.html', context)
        
        return render(request, 'failed.html', {
            'error': result.get('error', 'Payment validation failed'),
            'message': 'We could not validate your payment. Please contact support.',
            'success': False,
            'tran_id': tran_id
        })


@method_decorator(csrf_exempt, name='dispatch')
class PaymentFailedView(View):
    """Payment Failed Handler"""
    
    def get(self, request):
        return render(request, 'failed.html', {'error': 'Payment failed'})


@method_decorator(csrf_exempt, name='dispatch')
class PaymentCancelledView(View):
    """Payment Cancelled Handler"""
    
    def get(self, request):
        return render(request, 'cancelled.html')


@method_decorator(csrf_exempt, name='dispatch')
class PaymentIPNView(View):
    """SSLCommerz IPN Handler"""
    
    def post(self, request):
        ipn_data = request.POST.dict()
        logger.info(f"IPN Received: {ipn_data}")
        
        service = SSLCommerzPaymentService()
        result = service.validate_payment(ipn_data)
        
        if result.get('success'):
            logger.info(f"IPN validated for transaction: {ipn_data.get('tran_id')}")
        else:
            logger.warning(f"IPN validation failed: {result.get('error')}")
        
        return HttpResponse(status=200)


class CheckoutPageView(View):
    """Checkout Page"""
    
    def get(self, request):
        return render(request, 'checkout.html')