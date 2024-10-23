"""
Test for models.
"""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_user(email='test@example.com', password='test123'):
    """Helper function to create a user."""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Test for models."""

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful."""

        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['test2@Example.com', 'test2@example.com'],
            ['test3@ExamPLe.com', 'test3@example.com'],
            ['test4@Example.COM', 'test4@example.com']
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'test123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raise_error(self):
        """Test creating user without email raises error."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        """Test creating a new superuser."""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating a new recipe."""

        user = get_user_model().objects.create_user(
            'test@example.com',
            'test123'
        )

        recipe = models.Recipe.objects.create(
            user=user,
            title='Chocolate cake',
            time_minutes=30,
            price=Decimal('5.00'),
            description='Yummy chocolate cake'
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test creating a new tag."""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Vegan')

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """Test creating a new ingredient."""
        user = create_user()
        ingredient = models.Ingredient.objects.create(user=user, name='Cucumber')

        self.assertEqual(str(ingredient), ingredient.name)


