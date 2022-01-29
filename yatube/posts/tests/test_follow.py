from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Post, User


class FollowTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='follower')
        cls.user_author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user_author
        )

    def setUp(self) -> None:
        self.user_author_aut = Client()
        self.user_author_aut.force_login(self.user_author)
        self.user_follower_aut = Client()
        self.user_follower_aut.force_login(self.user_follower)

    def test_follow(self):
        """
        Проверяем, появляется ли подписка в базе, после подписки на автора
        """
        self.user_follower_aut.get(reverse(
            'posts:profile_follow', kwargs={
                'username': self.user_author.username}
        ))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_follower).filter(
                author=self.user_author).exists())

    def test_unfollow(self):
        """
        Проверяем, что подписки в базе нет, после отписки от автора
        """
        self.user_follower_aut.get(reverse(
            'posts:profile_unfollow', kwargs={
                'username': self.user_author.username}
        ))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_follower).filter(
                author=self.user_author).exists())

    def test_view_post_follow_index(self):
        """
        Проверяем, видел ли пост автора на странице подписок, если на него
        не подписаны, и если подписаны.
        """
        response = self.user_follower_aut.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post.text, response.content.decode())

        self.user_follower_aut.get(reverse(
            'posts:profile_follow', kwargs={
                'username': self.user_author.username}
        ))
        cache.clear()
        response_after_follow = self.user_follower_aut.get(
            reverse('posts:follow_index'))
        self.assertIn(self.post.text, response_after_follow.content.decode())
