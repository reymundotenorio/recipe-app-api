"""
Tests for the recipe API
"""
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': Decimal('5.00'),
        'description': 'Sample description',
        'link': 'https://sample.com'
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


def create_user(**params):
    """Create a sample user"""
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='testpass',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for user"""
        other_user = create_user(
            email='other@example.com',
            password='testpass',
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': Decimal('5.00'),
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        original_link = 'https://sample.com'
        recipe = create_recipe(
            user=self.user,
            title='Chicken tikka',
            link=original_link
        )

        payload = {
            'title': 'New Chicken tikka'
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        recipe = create_recipe(
            user=self.user,
            title='Spaghetti carbonara',
            link='https://sample.com',
            description='Sample description'
        )

        payload = {
            'title': 'Updated Spaghetti carbonara',
            'time_minutes': 25,
            'price': Decimal('7.00'),
            'link': 'https://updated.com',
            'description': 'Updated description'
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self):
        """Test that user cannot view other users' recipes"""
        new_user = create_user(
            email='new_user@example.com',
            password='testpass',
        )
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 60,
            'price': Decimal('20.00'),
            'tags': [{'name': 'Vegan'}, {'name': 'Dessert'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes.first()
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        for tag in payload['tags']:
            self.assertTrue(Tag.objects.filter(name=tag['name']).exists())

    def tes_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags"""
        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 60,
            'price': Decimal('20.00'),
            'tags': [{'name': 'Vegan'}, {'name': 'Dessert'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes.first()
        tags = recipe.tags.all()
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            self.assertIn(Tag.objects.get(name=tag['name']), tags)

    def test_create_tag_on_update(self):
        """Test creating a tag on recipe update"""
        recipe = create_recipe(user=self.user)

        payload = {
            'title': 'Updated recipe',
            'tags': [{'name': 'Vegan'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Vegan')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test updating a recipe with tags"""
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag1)

        tag2 = Tag.objects.create(user=self.user, name='Dessert')
        payload = {
            'tags': [{'name': 'Dessert'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag2, recipe.tags.all())
        self.assertNotIn(tag1, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing tags on recipe update"""
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag1)

        payload = {
            'tags': []
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with ingredients"""
        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 60,
            'price': Decimal('20.00'),
            'ingredients': [{'name': 'Avocado'}, {'name': 'Lime'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes.first()
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            self.assertTrue(Ingredient.objects.filter(
                name=ingredient['name'], user=self.user).exists())

    def test_create_recipe_with_existing_ingredients(self):
        """Test creating a recipe with existing ingredients"""
        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 60,
            'price': Decimal('20.00'),
            'ingredients': [{'name': 'Avocado'}, {'name': 'Lime'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes.first()
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            self.assertTrue(Ingredient.objects.filter(
                name=ingredient['name'], user=self.user).exists())

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient on recipe update"""
        recipe = create_recipe(user=self.user)

        payload = {
            'title': 'Updated recipe',
            'ingredients': [{'name': 'Salt'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='Salt')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test updating a recipe with ingredients"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Salt')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='Pepper')
        payload = {
            'ingredients': [{'name': 'Pepper'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing ingredients on recipe update"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Salt')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        payload = {
            'ingredients': []
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
