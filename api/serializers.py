from rest_framework import serializers
from .models import User, Product, Order, OrderItem
from django.db import transaction

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'is_staff']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name','description', 'price', 'stock']

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be a positive number.")
        return value
    

class OrderItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='product.name', read_only=True)
    price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2)

    class Meta:
        model = OrderItem
        fields = ('name', 'price', 'quantity', 'item_subtotal')


class OrderCreateSerializer(serializers.ModelSerializer):
    class OrderItemCreateSerializer(serializers.ModelSerializer):
        class Meta:
            model = OrderItem
            fields = ['product', 'quantity']

    order_id = serializers.UUIDField(read_only=True)
    items = OrderItemCreateSerializer(many=True, required=False)

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items')

        with transaction.atomic():
            instance = super().update(instance, validated_data)

            if items_data is not None:
                instance.items.all().delete()
                for item_data in items_data:
                    OrderItem.objects.create(order=instance, **item_data)

        return instance

    def create(self, validated_data):
        items_data = validated_data.pop('items')

        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            for item_data in items_data:
                OrderItem.objects.create(order=order, **item_data)
        return order

    class Meta:
        model = Order
        fields = ['order_id', 'user', 'status', 'items']
        extra_kwargs = {
            'user': {'read_only': True},
        }


class OrderSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(read_only=True)
    items = OrderItemSerializer(many=True)
    total_price = serializers.SerializerMethodField(method_name='total', read_only=True)

    def total(self, obj):
        order_items = obj.items.all()
        return sum(item.item_subtotal for item in order_items)

    class Meta:
        model = Order
        fields = ['order_id', 'user', 'created_at', 'status', 'items', 'total_price']


class ProductInfoSerializer(serializers.Serializer):
    products = ProductSerializer(many=True)
    count = serializers.IntegerField()
    max_price = serializers.FloatField()