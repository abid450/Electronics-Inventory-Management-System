"""
URL configuration for inventory project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from products.views import CategoryViewSet, ProductViewSet
from customers.views import CustomerViewSet
from Inventory_Tracking.views import *
from report.views import *
from django.views.generic import TemplateView
from checkout.views import *
from order.views import OrderViewSet
from cart.views import *


router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='products')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'customer', CustomerViewSet, basename='customer')
router.register(r'orders', OrderViewSet, basename='order')



urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),  
    path('silk/', include('silk.urls', namespace='silk')),

    path('dash_board/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('sales_report/', TemplateView.as_view(template_name='sales.html'), name='sales'), 
    path('products/', TemplateView.as_view(template_name='products.html'), name='products'),  
    path('product-details/', TemplateView.as_view(template_name='details.html'), name='product-details'),
    path('cart/', TemplateView.as_view(template_name='cart.html'), name='cart'),






    path('payment/checkout/', CheckoutPageView.as_view(), name='checkout'),
    path('checkout/success/', PaymentSuccessView.as_view(), name='checkout_success'),
    path('checkout/failed/', PaymentFailedView.as_view(), name='payment_failed'),
    path('checkout/cancelled/', PaymentCancelledView.as_view(), name='payment_cancelled'),
    path('checkout/ipn/', PaymentIPNView.as_view(), name='payment_ipn'),
    path('checkout/api/initiate/', checkout_initiate, name='payment_initiate'),
    path('api/cart/', CartAPIView.as_view(), name='cart'),
    path('api/cart/clear/', CartClearAPIView.as_view(), name='cart-clear'),
    path('api/cart/count/', CartCountAPIView.as_view(), name='cart-count'),




]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)