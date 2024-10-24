"""
Recipe serializers
"""

from rest_framework import serializers

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient objects"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name')
        read_only_fields = ('id',)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects"""

    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe objects"""
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'time_minutes', 'price', 'link', 'tags', 'ingredients',
        )
        read_only_fields = ('id',)

    def _get_or_create_tags(self, recipe, tags):
        """Create and return tags"""
        auth_user = self.context['request'].user

        for tag in tags:
            tag_obj = Tag.objects.get_or_create(user=auth_user, **tag)[0]
            recipe.tags.add(tag_obj)

    def _get_or_create_ingredients(self, recipe, ingredients):
        """Create and return ingredients"""
        auth_user = self.context['request'].user

        for ingredient in ingredients:
            ingredient_obj = Ingredient.objects.get_or_create(
                user=auth_user, **ingredient
            )[0]
            recipe.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)

        self._get_or_create_ingredients(recipe, ingredients)
        self._get_or_create_tags(recipe, tags)

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', [])

        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(instance, ingredients)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(instance, tags)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serialize a recipe detail"""

    class Meta:
        model = Recipe
        fields = RecipeSerializer.Meta.fields + ('description', 'image')


class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to recipes"""

    class Meta:
        model = Recipe
        fields = ('id', 'image')
        read_only_fields = ('id',)
        extra_kwargs = {
            'image': {'required': True},
        }
