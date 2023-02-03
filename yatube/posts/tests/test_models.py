from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=PostModelTest.user,
            text='Тестовый пост для проверки метода str',
        )

    def test_models_have_correct_object_names_text(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = PostModelTest.post
        text_str = post.text[:settings.LIMITATION_TEXT]
        self.assertEqual(text_str, post.__str__())

    def test_models_have_correct_object_names_group(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = PostModelTest.group
        group_str = group.title
        self.assertEqual(group_str, group.__str__())
