from django.shortcuts import render

# Create your views here.
# apps/customers/views.py

from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    """Customer Management ViewSet"""
    
    queryset = Customer.objects.filter(status='ACTIVE')
    serializer_class = CustomerSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'phone', 'customer_code']
    ordering_fields = ['created_at', 'total_purchased', 'loyalty_points']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Customer.objects.all()
        return Customer.objects.filter(status='ACTIVE')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)