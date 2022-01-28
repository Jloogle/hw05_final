import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


def get_context_first_obj_and_test(self,
                                   response,
                                   text,
                                   group=None,
                                   user=None,
                                   image=None):
    first_obj = response.context['page_obj'][0]
    first_text = first_obj.text
    self.assertEqual(first_text, text)
    if user:
        first_user = first_obj.author
        self.assertEqual(first_user, user)
    if group:
        first_group = first_obj.group
        self.assertEqual(first_group, group)
    if image:
        first_image = first_obj.image
        self.assertEqual(first_image, image)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем юзера
        cls.user = User.objects.create_user(username='author')
        # Создам первую группу
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug-1',
            description='Тестовое описание группы 1',
        )
        # Создаем вторую группу
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание группы 2',
        )
        cls.post = Post.objects.create(
            text='Текст тестового поста 1',
            author=cls.user,
            group=cls.group_1,
        )
        cls.post2 = Post.objects.create(
            text='Текст тестового поста 2',
            author=cls.user,
            group=cls.group_2,
        )
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
        cls.post3 = Post.objects.create(
            author=cls.user,
            group=cls.group_2,
            text='Текст тестового поста с картинкой',
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse(
                'posts:group_list',
                kwargs={'slug': self.group_1.slug})): 'posts/group_list.html',
            (reverse('posts:profile',
                     kwargs={'username': self.user})): 'posts/profile.html',
            (reverse('posts:post_detail',
                     kwargs={
                         'post_id': self.post.pk})): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            (reverse('posts:post_edit',
                     kwargs={
                         'post_id': self.post.pk})): 'posts/create_post.html',
        }
        # Проверяем, что при обращении к name вызывается соответствующий
        # HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:index'))
        get_context_first_obj_and_test(self,
                                       response,
                                       group=None,
                                       text=self.post3.text,
                                       image=self.post3.image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.post.group.slug})
        )
        get_context_first_obj_and_test(self,
                                       response,
                                       group=self.post.group,
                                       text=self.post.text,
                                       )
        response_2 = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.post3.group.slug})
        )
        get_context_first_obj_and_test(self,
                                       response_2,
                                       group=self.post3.group,
                                       text=self.post3.text,
                                       image=self.post3.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        get_context_first_obj_and_test(self,
                                       response,
                                       user=self.user,
                                       text=self.post3.text,
                                       image=self.post3.image
                                       )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон с детальной информацией поста имеет правильный контекст """
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post3.pk})
        )
        self.assertEqual(response.context['post'].text,
                         self.post3.text)
        self.assertEqual(response.context['post'].image,
                         self.post3.image)

    def test_post_create_page_show_correct_context(self):
        """Шаблон создания поста имеет правильный контекст"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }

        self.assertEqual(response.context['is_edit'], False)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон редактирования поста имеет правильный контекст"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context['is_edit'], True)

    def test_create_post_view_in_index_profile_group(self):
        """
        Проверяем, что созданный пост появляется на главной странице,
        странице с группой и на странице пользователя, создавшего пост
        """
        self.post4 = Post.objects.create(
            author=self.user,
            group=self.group_2,
            text='Новый тестовый пост 123'
        )
        response_index = self.client.get(reverse('posts:index'))
        self.assertEqual(response_index.context['page_obj'][0].text,
                         self.post4.text)
        response_profile = self.client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(response_profile.context['page_obj'][0].text,
                         self.post4.text)
        response_group = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_2.slug})
        )
        self.assertEqual(response_group.context['page_obj'][0].text,
                         self.post4.text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.posts_obj = []
        cls.user = User.objects.create_user(username='auth')
        # Создам первую группу
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug-1',
            description='Тестовое описание группы 1',
        )
        # Создаем вторую группу
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание группы 2',
        )
        # Создадим 15 записей в БД,
        # 12 записей 1 группы
        for i in range(1, 13):
            cls.posts_obj.append(
                Post(author=cls.user,
                     text=f'Текст тестового поста {i}',
                     group=cls.group_1, )
            )
        # 2 записи 2 группы
        for i in range(13, 15):
            cls.posts_obj.append(
                Post(author=cls.user,
                     text=f'Текст тестового поста {i}',
                     group=cls.group_2, )
            )
        # 1 запись без группы
        cls.posts_obj.append(
            Post(
                author=cls.user,
                text='Текст тестового поста 15', )
        )
        cls.posts = Post.objects.bulk_create(cls.posts_obj)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_paginaor(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         settings.POST_PER_PAGE)
        response2 = self.client.get(reverse('posts:index') + '?page=2')
        count_posts_page_2 = response2.context['page_obj'].paginator.count
        self.assertEqual(len(response2.context['page_obj']),
                         count_posts_page_2 - settings.POST_PER_PAGE)

    def test_profile_paginator(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(len(response.context['page_obj']),
                         settings.POST_PER_PAGE)
        response2 = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user}) + '?page=2')
        count_post_user = response2.context['page_obj'].paginator.count
        self.assertEqual(len(response2.context['page_obj']),
                         (count_post_user - settings.POST_PER_PAGE))

    def test_group_list_paginator(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug})
        )
        self.assertEqual(len(response.context['page_obj']),
                         settings.POST_PER_PAGE)
        response2 = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group_1.slug}) + '?page=2')
        count_post_group = response2.context['page_obj'].paginator.count
        self.assertEqual(len(response2.context['page_obj']),
                         (count_post_group - settings.POST_PER_PAGE))
