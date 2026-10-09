from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from ..models import Identity, Policy

class ViewsTestCase(APITestCase):
    def test_register(self)->None:
        url = reverse("register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "role": "user"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Identity.objects.filter(username="newuser").exists())

    def test_login(self)->None:
        Identity.objects.create_user(username="testuser", password="password123")
        url = reverse("login")
        response = self.client.post(url, {"username": "testuser", "password": "password123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_policy_crud_admin_only(self)->None:
        user = Identity.objects.create_user(username="testuser", password="password123", role="user")
        admin = Identity.objects.create_user(username="adminuser", password="password123", role="admin")
        
        url = reverse("policy-list")
        
        self.client.force_authenticate(user=user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        self.client.force_authenticate(user=admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
