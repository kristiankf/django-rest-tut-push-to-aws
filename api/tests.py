from api.models import User, Product
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status


class ProductAPITestCase(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass')
        self.normal_user = User.objects.create_user(username='user', password='userpass')
        self.product = Product.objects.create(
            name='Test Product',
            description='A product for testing',
            price=10.00,
            stock=100
        )
        self.url = reverse('product-detail', kwargs={'pk': self.product.pk})

    def test_get_product_detail(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], self.product.name)

    def test_unauthorized_update_product(self):
        data = {'name': 'Updated Product'}
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_delete_product(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_only_admin_can_delete_product(self):
        self.client.login(username='user', password='userpass')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

        self.client.login(username='admin', password='adminpass')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())


