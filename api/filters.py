import django_filters
from api.models import Product, Order
from rest_framework import filters

class ProductFilter(django_filters.FilterSet):
    class Meta:
        model = Product
        fields = {
            'name': ['icontains', 'iexact'], 
            'price': ['lt', 'gt', 'exact', 'range'],
            'stock': ['lt', 'gt', 'exact', 'range']
        }

class InStockFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(stock__gt=0)
    

class OrderFilter(django_filters.FilterSet):
    created_at = django_filters.DateFilter(field_name='created_at', lookup_expr='date')
    class Meta:
        model = Order
        fields = {
            'status': [ 'iexact', 'exact'], 
            'created_at': ['lt', 'gt', 'exact', 'range'],
        }