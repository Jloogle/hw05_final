from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTests(TestCase):
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
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self) -> None:
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_not_found(self):
        """Проверяем ответ на несуществующую страницу"""
        response = self.client.get('/not-exist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(adress=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_status_code_url_guest(self):
        """
        Проверка ответа страниц для неавторизованного пользователя
        """
        url_address_guest = {
            '/': 'Главная страница не отвечает',
            f'/group/{PostURLTests.group.slug}/': 'Страница постов группы'
                                                  ' не отвечает',
            f'/profile/{PostURLTests.user}/': 'Страница профиля пользователя'
                                              'не отвечает',
            f'/posts/{int(PostURLTests.post.id)}/': 'Страница подробной'
                                                    ' информации о посте '
                                                    'не отвечает'
        }
        for address, error_message in url_address_guest.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK,
                                 error_message)

    def test_status_code_url_authorized_user(self):
        """
        Проверка ответа страниц для авторизованного пользователя
        """
        url_address_authorized_user = {
            f'/posts/{int(PostURLTests.post.id)}/edit/': 'Страница '
                                                         'редактирования поста'
                                                         ' не отвечает',
            '/create/': 'Страница создания поста не отвечает'
        }
        for address, error_message in url_address_authorized_user.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK,
                                 error_message)
