from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse("recipe:ingredient-list")


class PublicIngredientsApiTests(TestCase):
    """Test public-facing ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving ingredients"""
        response = self.client.get(INGREDIENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test authenticated ingredients API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword", name="test"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredient_list(self):
        """Test retrieving a list of ingredients"""
        Ingredient.objects.create(user=self.user, name="ingredient1")
        Ingredient.objects.create(user=self.user, name="ingredient2")
        response = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test that ingredients returned are exclusive to the authenticated user"""
        other_user = get_user_model().objects.create_user(
            email="other@test.com", password="testpassword", name="other"
        )
        Ingredient.objects.create(user=other_user, name="other_ingredient")
        ingredient = Ingredient.objects.create(
            user=self.user, name="ingredient"
        )
        response = self.client.get(INGREDIENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], ingredient.name)

    def test_create_ingredient_successful(self):
        """Test creating a new ingredient"""
        payload = {"name": "ingredient"}
        response = self.client.post(INGREDIENTS_URL, payload)
        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload["name"],
        ).exists()
        self.assertTrue(exists)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_ingredient_invalid(self):
        """Test creating a ingredient with an invalid payload"""
        response = self.client.post(INGREDIENTS_URL, {"name": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipe(self):
        """Test filtering ingredients by those assigned to recipes"""
        ingredient1 = Ingredient.objects.create(
            user=self.user, name="ingredient1"
        )
        ingredient2 = Ingredient.objects.create(
            user=self.user, name="ingredient2"
        )
        recipe = Recipe.objects.create(
            user=self.user, title="recipe", time_minutes=1, price=1
        )
        recipe.ingredients.add(ingredient1)
        response = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})
        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_retrieve_ingredients_assigned_unique(self):
        """Test filtering ingredients by "assigned_only" returns unique items"""
        ingredient = Ingredient.objects.create(
            user=self.user, name="ingredient"
        )
        Ingredient.objects.create(user=self.user, name="other_ingredient")
        recipe1 = Recipe.objects.create(
            user=self.user, title="recipe1", time_minutes=1, price=1
        )
        recipe2 = Recipe.objects.create(
            user=self.user, title="recipe2", time_minutes=1, price=1
        )
        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)
        response = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})
        serializer = IngredientSerializer(ingredient)
        self.assertEqual(len(response.data), 1)
        self.assertIn(serializer.data, response.data)
