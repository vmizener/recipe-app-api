from rest_framework import serializers

from core.models import Ingredient, Recipe, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag class"""

    class Meta:
        model = Tag
        fields = ("id", "name")
        read_only_fields = ("id",)


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient class"""

    class Meta:
        model = Ingredient
        fields = ("id", "name")
        read_only_fields = ("id",)


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe class"""

    ingredients = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Ingredient.objects.all()
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "title",
            "ingredients",
            "tags",
            "time_minutes",
            "price",
            "link",
        )
        read_only_fields = ("id",)


class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for recipe image class"""

    class Meta:
        model = Recipe
        fields = ("id", "image")
        read_only_fields = ("id",)


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe details class"""

    ingredients = IngredientSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
