from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, Follow

User = get_user_model()
TEST_OF_POST: int = 13
small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B')
uploaded = SimpleUploadedFile(
    name='small.gif',
    content=small_gif,
    content_type='image/gif'
)


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.author = User.objects.create(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=PostModelTest.author,
            group=PostModelTest.group,
            text='Тестовый пост',
            image=uploaded,
        )
        cls.follow = Follow.objects.create(
            user=PostModelTest.user,
            author=PostModelTest.author,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostModelTest.user)
        self.author = Client()
        self.author.force_login(PostModelTest.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html':
                reverse('posts:group_list',
                        kwargs={'slug': f'{PostModelTest.group.slug}'}),
            'posts/profile.html':
                reverse('posts:profile',
                        kwargs={'username': f'{PostModelTest.author}'}),
            'posts/post_detail.html':
                reverse('posts:post_detail',
                        kwargs={'post_id': f'{PostModelTest.group.id}'}),
            'posts/create_post.html': reverse('posts:post_create')
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                error_name = f'Ошибка: {reverse_name}'
                self.assertTemplateUsed(response, template, error_name)

    def test_post_edit_uses_correct_template(self):
        """URL-адрес использует шаблон posts/create_post.html."""
        response = self.author.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': f'{PostModelTest.post.id}'}))
        error_name = 'Ошибка проверки по URL-адресу posts:post_edit'
        self.assertTemplateUsed(response, 'posts/create_post.html',
                                error_name)

    def context_functions(self, context):
        """Получаем содержимое context страниц."""
        self.assertEqual(context.id, PostModelTest.post.id)
        self.assertEqual(context.group.id, PostModelTest.post.group.id)
        self.assertEqual(context.author.id, PostModelTest.author.id)
        self.assertEqual(context.text, PostModelTest.post.text)
        self.assertEqual(context.group, PostModelTest.post.group)
        self.assertEqual(context.group.slug, PostModelTest.group.slug)
        self.assertEqual(context.author, PostModelTest.author)
        self.assertEqual(context.image, PostModelTest.post.image)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        context = response.context['page_obj'][0]
        self.context_functions(context)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': f'{PostModelTest.group.slug}'}))
        context = response.context['page_obj'][0]
        self.context_functions(context)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': f'{PostModelTest.author}'}))
        context = response.context['page_obj'][0]
        self.context_functions(context)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{PostModelTest.group.id}'}))
        post_text_0 = response.context['post'].text
        post_group_0 = response.context['post'].group
        post_author_0 = response.context['post'].author
        post_id_0 = response.context['post'].id
        post_image_0 = response.context['post'].image
        self.assertEqual(post_text_0, PostModelTest.post.text)
        self.assertEqual(post_group_0, PostModelTest.group)
        self.assertEqual(post_author_0, PostModelTest.author)
        self.assertEqual(post_id_0, PostModelTest.post.id)
        self.assertEqual(post_image_0, PostModelTest.post.image)

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': f'{PostModelTest.group.id}'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_added_works_correctly(self):
        """Пост при создании добавлен корректно"""
        cache.clear()
        post = PostModelTest.post
        response_index = self.authorized_client.get(
            reverse('posts:index'))
        response_group = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': f'{PostModelTest.group.slug}'}))
        response_profile = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': f'{PostModelTest.author}'}))
        index = response_index.context['page_obj']
        group = response_group.context['page_obj']
        profile = response_profile.context['page_obj']
        self.assertIn(post, index)
        self.assertIn(post, group)
        self.assertIn(post, profile)

    def test_cache_index_works_correctly(self):
        """Проверяем кеширование страницы index."""
        cache.clear()
        self.group = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        self.post = Post.objects.create(
            author=PostModelTest.author,
            group=PostModelTest.group,
            text='Тестовый пост2',
        )
        post_count = Post.objects.count()
        response = self.authorized_client.get(reverse('posts:index'))
        content_before = response.content
        Post.objects.filter(id=2).delete()
        post_count_after = Post.objects.count()
        content_after = response.content
        self.assertEqual(content_before, content_after)
        self.assertEqual(post_count, post_count_after + 1)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        new_post: list = []
        for i in range(TEST_OF_POST):
            new_post.append(Post(text=f'Тестовый текст {i}',
                            group=PaginatorViewsTest.group,
                            author=PaginatorViewsTest.user))
        Post.objects.bulk_create(new_post)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_correct_page_context_guest_client(self):
        '''Проверка количества постов на первой и второй страницах.'''
        cache.clear()
        pages = (reverse('posts:index'),
                 reverse('posts:profile',
                         kwargs={'username': f'{PaginatorViewsTest.user}'}),
                 reverse('posts:group_list',
                         kwargs={'slug': f'{PaginatorViewsTest.group.slug}'}))
        for page in pages:
            response1 = self.guest_client.get(page)
            response2 = self.guest_client.get(page + '?page=2')
            count_posts1 = len(response1.context['page_obj'])
            count_posts2 = len(response2.context['page_obj'])
            error_name1 = (f'Ошибка: {count_posts1} постов,'
                           f' должно {settings.POSTS_COUNT}')
            error_name2 = (f'Ошибка: {count_posts2} постов,'
                           f'должно {TEST_OF_POST -settings.POSTS_COUNT}')
            self.assertEqual(count_posts1,
                             settings.POSTS_COUNT,
                             error_name1)
            self.assertEqual(count_posts2,
                             TEST_OF_POST - settings.POSTS_COUNT,
                             error_name2)
