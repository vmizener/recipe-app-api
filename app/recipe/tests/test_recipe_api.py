from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe, Tag
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer

RECIPES_URL = reverse("recipe:recipe-list")


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
        url = detail_url(recipe.id)
        response = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(response.data, serializer.data)
