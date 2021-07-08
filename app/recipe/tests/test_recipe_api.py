import os.path
import tempfile

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from PIL import Image

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe, Tag
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer

RECIPES_URL = reverse("recipe:recipe-list")


def image_upload_url(recipe_id):
    """Return recipe image upload URL"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def sample_ingredient(user, name="ingredient"):
    """Create a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_tag(user, name="tag"):
    """Create a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_recipe(user, ingredients=None, tags=None, **kwargs):
    """Create a sample recipe"""
    defaults = {
        "title": "recipe",
        "time_minutes": 10,
        "price": 1.0,
    }
    defaults.update(kwargs)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test public-facing recipe API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving recipes"""
        response = self.client.get(RECIPES_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword", name="test"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        """Test retrieving recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)
        response = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test that recipes returned are exclusive to the authenticated user"""
        other_user = get_user_model().objects.create_user(
            email="other@test.com", password="testpassword", name="other"
        )
        sample_recipe(user=other_user)
        sample_recipe(user=self.user)
        response = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))
        response = self.client.get(detail_url(recipe.id))
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(response.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating a basic recipe"""
        payload = {
            "title": "recipe",
            "time_minutes": 1,
            "price": 1.0,
        }
        response = self.client.post(RECIPES_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data["id"])
        for key, value in payload.items():
            self.assertEqual(value, getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        tag1 = sample_tag(user=self.user, name="tag1")
        tag2 = sample_tag(user=self.user, name="tag2")
        payload = {
            "title": "recipe",
            "tags": [tag1.id, tag2.id],
            "time_minutes": 1,
            "price": 1.0,
        }
        response = self.client.post(RECIPES_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data["id"])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with ingredients"""
        ingredient1 = sample_ingredient(user=self.user, name="ingredient1")
        ingredient2 = sample_ingredient(user=self.user, name="ingredient2")
        payload = {
            "title": "recipe",
            "ingredients": [ingredient1.id, ingredient2.id],
            "time_minutes": 1,
            "price": 1.0,
        }
        response = self.client.post(RECIPES_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data["id"])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        """Test partially updating a recipe (PATCH request)"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name="new_tag")
        payload = {
            "title": "new_title",
            "tags": [new_tag.id],
        }
        self.client.patch(detail_url(recipe.id), payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test fully replacing a recipe (PUT request)"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {
            "title": "new_title",
            "time_minutes": 100,
            "price": 100.0,
        }
        self.client.put(detail_url(recipe.id), payload)
        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(value, getattr(recipe, key))
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 0)


class RecipeImageUploadTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword", name="test"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.recipe = sample_recipe(user=self.user)

    def test_upload_image_successful(self):
        """Test uploading an image to a recipe is successful"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            print(url, ntf)
            response = self.client.post(
                url, {"image": ntf}, format="multipart"
            )
        self.recipe.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image", response.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_invalid(self):
        """Test uploading an invalid image to a recipe"""
        url = image_upload_url(self.recipe.id)
        response = self.client.post(
            url, {"image": "not_an_image"}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        #  self.assertFalse(os.path.exists(self.recipe.image.path))

    def tearDown(self):
        self.recipe.image.delete()
