from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


class PublicUsersApiTests(TestCase):
    """Test public-facing users API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test that creating a user with a valid payload is successful"""
        payload = {
            "email": "test@test.com",
            "password": "testpassword",
            "name": "test",
        }
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**response.data)
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", response.data)

    def test_user_exists(self):
        """Test that creating a pre-existing user fails"""
        payload = {
            "email": "test@test.com",
            "password": "testpassword",
            "name": "test",
        }
        get_user_model().objects.create_user(**payload)

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that passwords must have a 5 character minimum length"""
        payload = {
            "email": "test@test.com",
            "password": "pw",
            "name": "test",
        }
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = (
            get_user_model().objects.filter(email=payload["email"]).exists()
        )
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for a user"""
        payload = {
            "email": "test@test.com",
            "password": "testpassword",
            "name": "test",
        }
        get_user_model().objects.create_user(**payload)
        response = self.client.post(TOKEN_URL, payload)
        self.assertIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test that a token is not created with invalid credentials"""
        get_user_model().objects.create_user(
            email="test@test.com", password="testpassword", name="test"
        )
        response = self.client.post(
            TOKEN_URL,
            {
                "email": "test@test.com",
                "password": "wrongpassword",
            },
        )
        self.assertNotIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that a token is not created if user doesn't exist"""
        response = self.client.post(
            TOKEN_URL,
            {
                "email": "test@test.com",
                "password": "testpassword",
            },
        )
        self.assertNotIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_fields(self):
        """Test that a token is not created if missing fields"""
        response = self.client.post(TOKEN_URL, {"email": "", "password": ""})
        self.assertNotIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that an auth token is required for users"""
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUsersApiTests(TestCase):
    """Test authenticated users API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword", name="test"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test that retrieving the profile for an authenticated user is successful"""
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {"name": self.user.name, "email": self.user.email},
        )

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed against the "me" URL"""
        response = self.client.post(ME_URL, {})
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_update_user_profile(self):
        """Test of updating the profile of an authenticated user"""
        payload = {"name": "new_name", "password": "newpassword"}
        response = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload["name"])
        self.assertTrue(self.user.check_password, payload["password"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
