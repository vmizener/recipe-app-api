from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer

TAGS_URL = reverse("recipe:tag-list")


class PublicTagsApiTests(TestCase):
    """Test public-facing tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving tags"""
        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test authenticated tags API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword", name="test"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags"""
        Tag.objects.create(user=self.user, name="tag1")
        Tag.objects.create(user=self.user, name="tag2")
        response = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are exclusive to the authenticated user"""
        other_user = get_user_model().objects.create_user(
            email="other@test.com", password="testpassword", name="other"
        )
        Tag.objects.create(user=other_user, name="other_tag")
        tag = Tag.objects.create(user=self.user, name="tag")
        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], tag.name)

    def test_create_tag_successful(self):
        """Test creating a new tag"""
        payload = {"name": "tag"}
        response = self.client.post(TAGS_URL, payload)
        exists = Tag.objects.filter(
            user=self.user,
            name=payload["name"],
        ).exists()
        self.assertTrue(exists)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_tag_invalid(self):
        """Test creating a tag with an invalid payload"""
        response = self.client.post(TAGS_URL, {"name": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
