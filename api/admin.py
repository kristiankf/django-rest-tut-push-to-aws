from django.contrib import admin
from .models import Product, Order, OrderItem, User

# Register your models here.
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]

admin.site.register(Order, OrderAdmin)
admin.site.register(Product)
admin.site.register(User)