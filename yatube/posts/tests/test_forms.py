import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from users.forms import CreationForm
from posts.forms import PostForm, CommentForm
from posts.models import Group, Post, Comment, User

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=PostFormTests.user,
            group=PostFormTests.group,
            text='Тестовый пост',
        )

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_help_text(self):
        text_help_text = PostFormTests.form.fields['text'].help_text
        group_help_text = PostFormTests.form.fields['group'].help_text
        self.assertEqual(text_help_text, 'Текст нового поста')
        self.assertEqual(group_help_text,
                         'Группа, к которой будет относиться пост')

    def test_create(self):
        """Валидная форма создает запись в create с картинкой."""
        post_count = Post.objects.count()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'group': PostFormTests.group.id,
            'text': 'Тестовый текст1',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username':
                                             f'{PostFormTests.user}'}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=PostFormTests.group.id,
                text=form_data['text'],
                author=PostFormTests.user,
                image='posts/small.gif',
            ).exists()
        )

    def test_edit_post(self):
        """Редактирование поста происходит корректно."""
        post_count = Post.objects.count()
        self.new_group = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        form_data = {
            'group': self.new_group.id,
            'text': 'Новый текст',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': f'{PostFormTests.post.id}'}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                id=PostFormTests.post.id,
                group=self.new_group.id,
                text=form_data['text'],
                author=PostFormTests.user,
            ).exists()
        )


class SignupFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.form = CreationForm()

    def setUp(self):
        self.guest_client = Client()

    def test_singnup(self):
        """Проверка регистрации нового пользователя."""
        form_data = {
            'first_name': 'User',
            'last_name': 'Newuser',
            'username': 'usernina',
            'email': 'User14@mail.ru',
            'password1': '1412yatube',
            'password2': '1412yatube',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:index'))
        self.assertTrue(
            User.objects.filter(
                first_name=form_data['first_name'],
                last_name=form_data['last_name'],
                username=form_data['username'],
                email=form_data['email']
            ).exists()
        )


class CommentFormTests(TestCase):
    """Комментарии появляются на странице поста."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='author')
        cls.post = Post.objects.create(
            author=CommentFormTests.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            text='Текст комментария',
            author=CommentFormTests.user,
            post=CommentFormTests.post,
        )
        cls.form = CommentForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentFormTests.user)

    def test_comment_works_correctly(self):
        form_data = {
            'text': 'Текст комментария',
            'author': CommentFormTests.user,
            'post': CommentFormTests.post
        }
        self.authorized_client.post(
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{CommentFormTests.post.id}'}),
            data=form_data,
            follow=True,
        )
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                author=CommentFormTests.user,
                post=CommentFormTests.post
            ).exists()
        )
