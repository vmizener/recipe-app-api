from rest_framework import serializers

from core.models import Ingredient, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags class"""

    class Meta:
        model = Tag
        fields = ("id", "name")
        read_only_fields = ("id",)


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients class"""

    class Meta:
        model = Ingredient
        fields = ("id", "name")
        read_only_fields = ("id",)
