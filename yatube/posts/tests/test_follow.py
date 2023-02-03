from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, Follow

User = get_user_model()
TEST_OF_POST: int = 13


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.user2 = User.objects.create(username='user_not_subscriber')
        cls.author = User.objects.create(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=PostModelTest.author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostModelTest.user)
        self.client = Client()
        self.client.force_login(PostModelTest.user2)

    def test_authorized_follows(self):
        """Авторизованный пользователь может подписываться на других
        пользователей."""
        Follow.objects.all().delete()
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': PostModelTest.author}))
        self.assertTrue(Follow.objects.filter(
            user=PostModelTest.user,
            author=PostModelTest.author,
        ).exists()
        )

    def test_authorized_unfollows(self):
        """Авторизованный пользователь может отписываться от других
        пользователей."""
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': PostModelTest.author}))
        self.assertTrue(Follow.objects.filter(
            user=PostModelTest.user,
            author=PostModelTest.author,
        ).exists()
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': PostModelTest.author}))
        self.assertFalse(Follow.objects.filter(
            user=PostModelTest.user,
            author=PostModelTest.author,
        ).exists()
        )

    def test_follow_index(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан"""
        Follow.objects.create(user=PostModelTest.user,
                              author=PostModelTest.author)
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        context_post = response.context['page_obj'][0]
        self.assertEqual(context_post.id, PostModelTest.post.id)
        self.assertEqual(context_post.text, PostModelTest.post.text)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_follow_index(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан"""
        response = self.client.get(
            reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
