from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from api.models import Product
from django.core.cache import cache

@receiver([post_save, post_delete], sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    """
    Invalidate the cache for product listings when a Product is created, updated, or deleted.
    """
    print("Clearing product list cache")

    # cache.delete('product_list_cache')

    cache.delete_pattern('*product_list*')

