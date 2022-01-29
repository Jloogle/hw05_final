import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.user2 = User.objects.create_user(username='NotAuthor')
        # Создаем запись в базе данных
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание группы 2'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            group=cls.group,
            author=cls.user,
        )
        cls.form = PostForm()
        cls.comment_form = CommentForm()

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем второго авторизованного клиента
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_signup_form(self):
        """Форма создаёт юзера и делает редирект на главную страницу"""
        user_count = User.objects.count()
        user_data = {
            'first_name': 'User',
            'last_name': 'Userovich',
            'username': 'UserUserUser',
            'email': 'userUser@mail.ru',
            'password1': 'UserUser123321@',
            'password2': 'UserUser123321@'
        }
        response = self.client.post(
            reverse('users:signup'),
            data=user_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), user_count + 1)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_create_post_form(self):
        """Проверка, что пост может создать авторизованный пользователь"""
        count_post = Post.objects.count()
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
            'text': 'Новый тестовый текст',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.user.username}))
        self.assertEqual(Post.objects.count(), count_post + 1)
        post_last = Post.objects.order_by('-id', '-pub_date').first()
        self.assertEqual(post_last.image.name,
                         ('posts/' + form_data['image'].name),
                         'Картинка созданного поста и последнего не совпадает')
        self.assertEqual(post_last.text, form_data['text'],
                         'Текст созданного поста и последнего не совпадает')
        self.assertEqual(post_last.group.id, form_data['group'],
                         'Группа созданного поста и последнего не совпадает')

    def test_post_edit_form(self):
        """Проверка, что автор поста может отредактировать его"""
        form_data = {
            'text': 'Ультрановый тестовый текст',
            'group': self.group2.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True)
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.pk}))
        self.post.refresh_from_db()

        self.assertEqual(self.post.text, form_data['text'])
        self.assertEqual(self.post.group.id, form_data['group'])

    def test_guest_create_post(self):
        """Проверка, что пост не может создать гость"""
        count_post = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст гостя',
            'group': self.group2.id
        }
        self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), count_post)

    def test_guest_edit_post(self):
        """Проверка, что пост не может отредактировать гость"""
        form_data = {
            'text': 'Тестовый текст гостя',
            'group': self.group2.id
        }
        self.client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True)
        self.post.refresh_from_db()
        self.assertNotEqual(self.post.text, form_data['text'])
        self.assertNotEqual(self.post.group.id, form_data['group'])

    def test_not_author_edit_post(self):
        """Проверка, что пост не может отредактировать не автор"""
        form_data = {
            'text': 'Отредактирвал не автор',
            'group': self.group2.id
        }
        self.authorized_client2.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.post.refresh_from_db()
        self.assertNotEqual(self.post.text, form_data['text'])
        self.assertNotEqual(self.post.group.id, form_data['group'])

    def test_guest_cant_add_comment(self):
        """
        Проверка, что количество постов не меняется, если его
        пытается создать неавторизованный пользователь
        """
        comments_count = Comment.objects.filter(id=self.post.pk).count()
        comment_form_data = {
            'text': 'Новый комментарий гостя',
            'post_id': self.post.pk
        }
        self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=comment_form_data,
            follow=True
        )
        self.assertEqual(
            Comment.objects.filter(id=self.post.pk).count(), comments_count)

    def test_authorized_client_cant_add_comment(self):
        """Проверка создания поста и появления его на странице поста"""
        comments_count = Comment.objects.filter(id=self.post.pk).count()
        comment_form_data = {
            'text': 'Новый комментарий',
            'post_id': self.post.pk
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=comment_form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.pk}))
        self.assertEqual(
            Comment.objects.filter(id=self.post.pk).count(),
            comments_count + 1)
        response_post_with_comment = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertIn(comment_form_data['text'],
                      response_post_with_comment.content.decode())
