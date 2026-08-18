# apps/products/views.py

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F
from django.shortcuts import get_object_or_404
from .models import Category, Product
from .serializers import *



class ProductViewSet(viewsets.ModelViewSet):
    """Product CRUD with stock management"""
    
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sku', 'barcode']
    ordering_fields = ['name', 'selling_price', 'quantity', 'created_at']
    filterset_fields = ['category', 'is_active', 'is_featured', 'is_new', 'is_best_seller']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """
        ✅ ProductDetailView - Complete product details with all fields
        GET: /api/products/{id}/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Get related products (same category)
        related_products = Product.objects.filter(
            category=instance.category,
            is_active=True
        ).exclude(id=instance.id)[:4]
        
        return Response({
            'success': True,
            'data': {
                'product': serializer.data,
                'related_products': ProductSerializer(related_products, many=True).data,
            }
        })

    
    # Details Page ---------------------------------------------------------
    @action(detail=True, methods=['get'], url_path='detail')
    def product_detail(self, request, pk=None):
        """
        ✅ ProductDetailView - Custom action for product details
        GET: /api/products/{id}/detail/
        """
        product = self.get_object()
        serializer = ProductDetailSerializer(product)
        
        # Related products
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        
        return Response({
            'success': True,
            'data': {
                'product': serializer.data,
                'related_products': ProductSerializer(related_products, many=True).data,
            }
        })
    
    
    # ============================================
    # Product Specifications
    # ============================================
    @action(detail=True, methods=['get'], url_path='specifications')
    def get_specifications(self, request, pk=None):
        """Get product specifications"""
        product = self.get_object()
        specs = product.specifications or {}
        
        spec_list = [
            {'key': key, 'value': value}
            for key, value in specs.items()
            if key and value
        ]
        
        return Response({
            'success': True,
            'data': spec_list
        })
    
    # ============================================
    # Other Actions
    # ============================================
    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        """Update product stock"""
        product = self.get_object()
        quantity = request.data.get('quantity')
        
        if quantity is None:
            return Response(
                {'error': 'Quantity is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product.quantity = int(quantity)
            product.save()
            return Response({
                'success': True,
                'message': 'Stock updated successfully',
                'quantity': product.quantity
            })
        except ValueError:
            return Response(
                {'error': 'Invalid quantity value'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get all low stock products"""
        products = Product.objects.filter(
            quantity__lte=F('min_stock_level'),
            is_active=True
        )
        serializer = self.get_serializer(products, many=True)
        return Response({
            'count': products.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Get all out of stock products"""
        products = Product.objects.filter(
            quantity=0,
            is_active=True
        )
        serializer = self.get_serializer(products, many=True)
        return Response({
            'count': products.count(),
            'results': serializer.data
        })


class CategoryViewSet(viewsets.ModelViewSet):
    """Category CRUD"""
    
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']