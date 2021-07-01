from django.contrib.auth import get_user_model
from django.test import TestCase


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
