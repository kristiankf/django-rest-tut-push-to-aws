from django.db.models import Max
from django.db.models.functions import Lower
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers, vary_on_cookie

from rest_framework.decorators import action
from rest_framework import filters, generics, viewsets
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle

from api.filters import InStockFilterBackend, OrderFilter, ProductFilter
from api.models import Order, OrderItem, Product, User
from api.serializers import (OrderSerializer, ProductInfoSerializer,
                             ProductSerializer, OrderCreateSerializer, UserSerializer)
from api.tasks import send_order_confirmation_email


class ProductListCreateAPIView(generics.ListCreateAPIView):
    throttle_scope = 'products'
    throttle_classes = [ScopedRateThrottle]
    queryset = Product.objects.order_by('pk')
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    filter_backends = [
        DjangoFilterBackend, 
        filters.SearchFilter, 
        filters.OrderingFilter, 
        # InStockFilterBackend
    ]
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'name', 'id', 'stock', 'name_l']
    pagination_class = PageNumberPagination
    pagination_class.page_size = 2
    pagination_class.page_size_query_param = 'page_size'
    pagination_class.max_page_size = 6

    @method_decorator(cache_page(60*15, key_prefix='product_list'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_permissions(self):
        self.permission_classes = [IsAdminUser] if self.request.method == 'POST' else [AllowAny]
        return super().get_permissions()

    def get_queryset(self):
        import time
        time.sleep(2)  # Simulate a slow query for demonstration
        qs = super().get_queryset()
        qs = qs.annotate(name_l=Lower('name'))
        return qs


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        self.permission_classes = [IsAdminUser] if self.request.method in ['PUT', 'PATCH', 'DELETE'] else [AllowAny]
        return super().get_permissions()
    

# class OrderListAPIView(generics.ListAPIView):
#     queryset = Order.objects.prefetch_related('items__product')
#     serializer_class = OrderSerializer


# class UserOrderListAPIView(generics.ListAPIView):
#     queryset = Order.objects.prefetch_related('items__product')
#     serializer_class = OrderSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         user = self.request.user
#         qs = super().get_queryset()
#         return qs.filter(user=user)

class OrderViewSet(viewsets.ModelViewSet):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'orders'
    queryset = Order.objects.prefetch_related('items__product')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filterset_class = OrderFilter
    filter_backends = [DjangoFilterBackend]

    @method_decorator(cache_page(60*15, key_prefix='order_list'))
    @method_decorator(vary_on_headers("Authorization"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)
        send_order_confirmation_email.delay(order.order_id, self.request.user.email)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return OrderCreateSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs

    # @action(detail=False, methods=['get'], url_path='user-orders')
    # def user_orders(self, request):
    #     orders = self.get_queryset().filter(user=request.user)
    #     serializer = self.get_serializer(orders, many=True)
    #     return Response(serializer.data)





class ProductInfoAPIView(APIView):
    def get(self, request, *args, **kwargs):
        products = Product.objects.all()
        serializer = ProductInfoSerializer({
            'products': products,
            'count': products.count(),
            'max_price': products.aggregate(max_price=Max('price'))['max_price']
        })
        return Response(serializer.data)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = None
