from django.shortcuts import render

# Create your views here.
# apps/orders/views.py

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count

from .models import Order, OrderItem
from .serializers import (
    OrderSerializer, OrderCreateSerializer,
    OrderStatusUpdateSerializer, OrderListSerializer
)
from products.models import Product


class OrderViewSet(viewsets.ModelViewSet):
    """
    Order Management ViewSet
    - List orders
    - Create order from checkout
    - Update order status
    - Cancel order
    - Order statistics
    """
    
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]  # Public for testing
    search_fields = ['order_number', 'customer_name', 'customer_email']
    ordering_fields = ['created_at', 'total', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return Order.objects.all()
        return Order.objects.all()  # Public for testing
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create order from checkout with items
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # ============================================
        # Calculate Total from Items
        # ============================================
        subtotal = 0
        items_data = []
        
        for item in data['items']:
            product = get_object_or_404(Product, id=item['product_id'])
            
            # Check stock
            if product.quantity < item['quantity']:
                return Response({
                    'success': False,
                    'message': f"Insufficient stock for {product.name}",
                    'errors': {'items': f"{product.name} has only {product.quantity} in stock"}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            unit_price = item.get('unit_price', product.selling_price)
            total_price = unit_price * item['quantity']
            subtotal += total_price
            
            items_data.append({
                'product': product,
                'quantity': item['quantity'],
                'unit_price': unit_price,
                'total_price': total_price,
            })
        
        tax_amount = subtotal * 0.05
        shipping_cost = 100
        total = subtotal + tax_amount + shipping_cost
        
        # ============================================
        # Create Order
        # ============================================
        order = Order.objects.create(
            customer_name=data['customer_name'],
            customer_email=data['customer_email'],
            customer_phone=data['customer_phone'],
            customer_address=data.get('customer_address', ''),
            customer_city=data.get('customer_city', ''),
            payment_method=data['payment_method'],
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            total=total,
            notes=data.get('notes', '')
        )
        
        # Create order items
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price']
            )
        
        return Response({
            'success': True,
            'message': 'Order created successfully',
            'data': OrderSerializer(order).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update order status
        """
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        old_status = order.status
        
        # Validate status transition
        if old_status == 'CANCELLED' and new_status != 'CANCELLED':
            return Response({
                'success': False,
                'message': 'Cannot change status of cancelled order'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = new_status
        order.save()
        
        return Response({
            'success': True,
            'message': f'Order status updated from {old_status} to {new_status}',
            'data': OrderSerializer(order).data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel order and restore stock
        """
        order = self.get_object()
        
        if order.status in ['DELIVERED', 'CANCELLED']:
            return Response({
                'success': False,
                'message': f'Order cannot be cancelled. Current status: {order.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Restore stock for sales order
        for item in order.items.all():
            product = item.product
            product.quantity += item.quantity
            product.save()
        
        order.status = 'CANCELLED'
        order.save()
        
        return Response({
            'success': True,
            'message': f'Order {order.order_number} cancelled successfully'
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get order statistics
        """
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='PENDING').count()
        processing_orders = Order.objects.filter(status='PROCESSING').count()
        completed_orders = Order.objects.filter(status='DELIVERED').count()
        cancelled_orders = Order.objects.filter(status='CANCELLED').count()
        
        total_revenue = Order.objects.filter(
            status='DELIVERED'
        ).aggregate(total=Sum('total'))['total'] or 0
        
        return Response({
            'success': True,
            'data': {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'processing_orders': processing_orders,
                'completed_orders': completed_orders,
                'cancelled_orders': cancelled_orders,
                'total_revenue': total_revenue,
            }
        })