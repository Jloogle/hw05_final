from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from ..models import Group, Post, User


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )

    def test_index_cache(self):
        """
        Проверка, что созданный пост появляется не сразу на главной странице
        """
        self.post = Post.objects.create(
            text='Проверка кэша',
            group=self.group,
            author=self.user
        )
        response_first = self.client.get(reverse('posts:index'))
        self.assertContains(response_first, self.post.text)

        self.post_2 = Post.objects.create(
            text='Тест кэша',
            group=self.group,
            author=self.user
        )
        response_second = self.client.get(reverse('posts:index'))
        self.assertNotContains(response_second, self.post_2.text)
        cache.clear()
        response_third = self.client.get(reverse('posts:index'))
        self.assertContains(response_third, self.post_2.text)
