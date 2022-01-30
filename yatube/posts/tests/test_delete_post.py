from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, User


class PostDeleteTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user
        )

    def setUp(self) -> None:
        self.user_auth = Client()
        self.user_auth.force_login(self.user)

    def test_delete_post_guest(self):
        """
        Поверка, про не автор не может удалить пост
        """
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'][0].text, self.post.text)
        self.client.get(reverse('posts:post_delete',
                                kwargs={'post_id': self.post.pk}))
        cache.clear()
        response_after_del = self.client.get(reverse('posts:index'))
        self.assertEqual(
            response_after_del.context['page_obj'][0].text, self.post.text)
        self.assertEqual(
            (self.client.get(reverse(
                'posts:post_delete',
                kwargs={'post_id': self.post.pk}))).status_code,
            HTTPStatus.FOUND
        )

    def test_delete_post(self):
        """
        Проверка, что автор может удалить пост
        """
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'][0].text, self.post.text)
        self.user_auth.get(reverse('posts:post_delete',
                                   kwargs={'post_id': self.post.pk}))
        cache.clear()
        response_after = self.client.get(reverse('posts:index'))
        self.assertNotIn(self.post.text, response_after.content.decode())
