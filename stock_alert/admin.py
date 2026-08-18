from django.contrib import admin

# Register your models here.
# apps/stock/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import StockAlert


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['product', 'current_quantity', 'min_level', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['product__name', 'product__sku']
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True)
    mark_as_resolved.short_description = "Mark selected alerts as resolved"