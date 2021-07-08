from django.contrib.auth import get_user_model
from django.test import TestCase

from core import models


def sample_user(email="test@test.com", password="testpassword"):
    """Create a sample user"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        """Test that creating a new user with an email is successful"""
        email = "test@test.com"
        password = "password"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEquals(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test that the email for a new user is normalized"""
        email = "test@TEST.com"
        user = get_user_model().objects.create_user(email, "password")

        self.assertEquals(user.email, email.lower())

    def test_new_user_no_email(self):
        """Test that creating a user with no email raises an error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, "password")

    def test_create_new_superuser(self):
        """Test that creating a new superuser is successful"""
        user = get_user_model().objects.create_superuser(
            "test@test.com",
            "password",
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test the tag string representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name="tag",
        )
        self.assertEqual(str(tag), tag.name)
