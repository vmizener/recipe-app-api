from rest_framework import (
    authentication,
    decorators,
    mixins,
    permissions,
    response,
    status,
    viewsets,
)

from core.models import Ingredient, Recipe, Tag
from recipe import serializers


class BaseRecipeAttrViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin
):
    """Base viewset for user-owned recipe attributes"""

    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Return attributes for the current authenticated user only"""
        queryset = self.queryset
        if int(self.request.query_params.get("assigned_only", 0)):
            queryset = queryset.filter(recipe__isnull=False)
        return (
            queryset.filter(user=self.request.user)
            .distinct()
            .order_by("-name")
        )

    def perform_create(self, serializer):
        """Create a new attribute"""
        serializer.save(user=self.request.user)


class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags in the database"""

    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients in the database"""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Manage recipes in the database"""

    queryset = Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def __params_to_ints(self, qs):
        """Convert a list of string IDs to integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Return recipes for the current authenticated user only"""
        queryset = self.queryset
        for attr in ["tags", "ingredients"]:
            if params := self.request.query_params.get(attr):
                param_ids = self.__params_to_ints(params)
                queryset = queryset.filter(**{f"{attr}__id__in": param_ids})
        return queryset.filter(user=self.request.user).order_by("-title")

    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == "retrieve":
            return serializers.RecipeDetailSerializer
        elif self.action == "upload_image":
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)

    @decorators.action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload an image to a recipe"""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return response.Response(
                serializer.data, status=status.HTTP_200_OK
            )
        return response.Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )
