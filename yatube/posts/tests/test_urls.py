from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.author = User.objects.create(username='Nina')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=PostURLTest.author,
            group=PostURLTest.group,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTest.user)
        self.author = Client()
        self.author.force_login(PostURLTest.author)

        self.url_for_all_users = {
            '/': 'posts/index.html',
            f'/group/{PostURLTest.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTest.author}/': 'posts/profile.html',
            f'/posts/{PostURLTest.post.id}/': 'posts/post_detail.html',
        }

    def test_url(self):
        """Страницы доступные любому пользователю."""
        for field, _ in self.url_for_all_users.items():
            with self.subTest(field=field):
                response = self.client.get(field)
                error_name = f'Ошибка: нет доступа до страницы {field}'
                self.assertEqual(response.status_code,
                                 HTTPStatus.OK, error_name)

    def test_url_create_for_authorized_client(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        error_name = 'Ошибка: нет доступа до страницы create'
        self.assertEqual(response.status_code, HTTPStatus.OK, error_name)

    def test_url_posts_edit_for_author(self):
        """Страница posts_edit доступна автору пользователю."""
        response = self.author.get(f'/posts/{PostURLTest.post.id}/edit/')
        error_name = 'Ошибка: нет доступа до страницы posts_edit'
        self.assertEqual(response.status_code, HTTPStatus.OK, error_name)

    def test_unknown_url(self):
        """Страница неизвестного ulr."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_error_page(self):
        """Проверка работы страницы ошибки 404."""
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_for_all_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        for address, template in self.url_for_all_users.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                error_name = f'Ошибка: {address} ожидал шаблон {template}'
                self.assertTemplateUsed(response, template, error_name)

    def test_template_create_for_authorized(self):
        """URL-адрес create использует соответствующий шаблон."""
        response = self.authorized_client.get('/create/')
        error_name = 'Ошибка: нет доступа до страницы /create/'
        self.assertTemplateUsed(response, 'posts/create_post.html',
                                error_name)

    def test_template_posts_edit_for_author(self):
        """URL-адрес использует соответствующий шаблон."""
        response = self.author.get(
            f'/posts/{PostURLTest.post.id}/edit/')
        error_name = 'Ошибка: нет доступа до страницы posts_id_edit'
        self.assertTemplateUsed(response,
                                'posts/create_post.html', error_name)
