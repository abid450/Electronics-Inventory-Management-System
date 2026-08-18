from django.shortcuts import render

# Create your views here.
# apps/cart/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Cart, CartItem
from products.models import Product
from .serializers import (
    AddToCartSerializer, UpdateCartSerializer,
    RemoveFromCartSerializer, CartSerializer
)
import logging

logger = logging.getLogger(__name__)


class CartAPIView(APIView):
    """
    Professional Cart Management API with Database Storage
    """
    
    permission_classes = [AllowAny]
    
    def _get_or_create_cart(self, request):
        """Get or create cart for user or session"""
        if request.user and request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
            # Migrate session cart to user cart if exists
            if request.session.get('cart_session_id'):
                try:
                    session_cart = Cart.objects.get(id=request.session['cart_session_id'])
                    if session_cart and session_cart != cart:
                        # Move items from session cart to user cart
                        for item in session_cart.items.all():
                            cart_item, _ = CartItem.objects.get_or_create(
                                cart=cart,
                                product=item.product,
                                defaults={'quantity': 0}
                            )
                            cart_item.quantity += item.quantity
                            cart_item.save()
                        session_cart.delete()
                except Cart.DoesNotExist:
                    pass
                del request.session['cart_session_id']
            return cart
        else:
            # Anonymous user - use session
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            
            cart, created = Cart.objects.get_or_create(session_key=session_key)
            if created:
                request.session['cart_session_id'] = str(cart.id)
            return cart
    
    def get(self, request):
        """Get current cart"""
        try:
            cart = self._get_or_create_cart(request)
            serializer = CartSerializer(cart, context={'request': request})
            
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Cart GET error: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request):
        """Add item to cart"""
        try:
            serializer = AddToCartSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors,
                    'message': 'Validation failed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            product = get_object_or_404(Product, id=data['product_id'], is_active=True)
            
            # Check stock
            if product.quantity < data['quantity']:
                return Response({
                    'success': False,
                    'message': f'Insufficient stock. Available: {product.quantity}',
                    'data': {'available': product.quantity}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            cart = self._get_or_create_cart(request)
            
            # Add or update item
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': data['quantity']}
            )
            
            if not created:
                new_quantity = cart_item.quantity + data['quantity']
                if product.quantity < new_quantity:
                    return Response({
                        'success': False,
                        'message': f'Insufficient stock. Available: {product.quantity}',
                        'data': {'available': product.quantity}
                    }, status=status.HTTP_400_BAD_REQUEST)
                cart_item.quantity = new_quantity
                cart_item.save()
            
            return Response({
                'success': True,
                'message': f'{product.name} added to cart',
                'data': {
                    'cart': cart.get_items_data(),
                    'total_items': cart.get_total_items(),
                    'total_price': cart.get_total_price(),
                    'item_added': {
                        'product_id': str(product.id),
                        'name': product.name,
                        'quantity': data['quantity'],
                        'price': float(product.selling_price)
                    }
                }
            }, status=status.HTTP_200_OK)
            
        except Product.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Product not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Cart POST error: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def put(self, request):
        """Update item quantity"""
        try:
            serializer = UpdateCartSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors,
                    'message': 'Validation failed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            cart = self._get_or_create_cart(request)
            
            cart_item = get_object_or_404(CartItem, cart=cart, product_id=data['product_id'])
            
            # If quantity is 0, remove item
            if data['quantity'] == 0:
                cart_item.delete()
                return Response({
                    'success': True,
                    'message': 'Item removed from cart',
                    'data': {
                        'cart': cart.get_items_data(),
                        'total_items': cart.get_total_items(),
                        'total_price': cart.get_total_price()
                    }
                }, status=status.HTTP_200_OK)
            
            # Validate stock
            if cart_item.product.quantity < data['quantity']:
                return Response({
                    'success': False,
                    'message': f'Insufficient stock. Available: {cart_item.product.quantity}',
                    'data': {'available': cart_item.product.quantity}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            cart_item.quantity = data['quantity']
            cart_item.save()
            
            return Response({
                'success': True,
                'message': 'Cart updated',
                'data': {
                    'cart': cart.get_items_data(),
                    'total_items': cart.get_total_items(),
                    'total_price': cart.get_total_price()
                }
            }, status=status.HTTP_200_OK)
            
        except CartItem.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Item not found in cart'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Cart PUT error: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def delete(self, request):
        """Remove item from cart"""
        try:
            serializer = RemoveFromCartSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors,
                    'message': 'Validation failed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            cart = self._get_or_create_cart(request)
            
            cart_item = get_object_or_404(CartItem, cart=cart, product_id=data['product_id'])
            cart_item.delete()
            
            return Response({
                'success': True,
                'message': 'Item removed from cart',
                'data': {
                    'cart': cart.get_items_data(),
                    'total_items': cart.get_total_items(),
                    'total_price': cart.get_total_price()
                }
            }, status=status.HTTP_200_OK)
            
        except CartItem.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Item not found in cart'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Cart DELETE error: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# apps/cart/views.py

class CartClearAPIView(APIView):
    """Clear entire cart - Also clears session"""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # Clear database cart
            if request.user and request.user.is_authenticated:
                cart = Cart.objects.filter(user=request.user).first()
                if cart:
                    cart.clear()
                    cart.delete()
            
            # Clear session cart
            if request.session.get('cart'):
                request.session['cart'] = {}
                request.session.modified = True
            
            # Clear session cart ID
            if request.session.get('cart_session_id'):
                try:
                    cart = Cart.objects.get(id=request.session['cart_session_id'])
                    cart.clear()
                    cart.delete()
                except Cart.DoesNotExist:
                    pass
                del request.session['cart_session_id']
            
            return Response({
                'success': True,
                'message': 'Cart cleared successfully',
                'data': {
                    'cart': [],
                    'total_items': 0,
                    'total_price': 0
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Cart clear error: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CartCountAPIView(APIView):
    """Get cart item count"""
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            if request.user and request.user.is_authenticated:
                cart = Cart.objects.filter(user=request.user).first()
            else:
                session_key = request.session.session_key
                if not session_key:
                    return Response({
                        'success': True,
                        'data': {'count': 0}
                    }, status=status.HTTP_200_OK)
                cart = Cart.objects.filter(session_key=session_key).first()
            
            count = cart.get_total_items() if cart else 0
            
            return Response({
                'success': True,
                'data': {'count': count}
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Cart count error: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)