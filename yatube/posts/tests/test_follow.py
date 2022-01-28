from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, User


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

    def test_follow_and_unfollow(self):
        """
        Проверяем, увеличивается ли количество подписчиков у автора после
        подписки на него, и уменьшается ли после отписки.
        """
        follow_count = self.user_author.following.count()
        self.user_follower_aut.get(reverse(
            'posts:profile_follow', kwargs={
                'username': self.user_author.username}
        ))
        follow_count_after = self.user_author.following.count()
        self.assertEqual(follow_count_after, follow_count + 1)

        self.user_follower_aut.get(reverse(
            'posts:profile_unfollow', kwargs={
                'username': self.user_author.username}
        ))
        follow_count_after_unfollow = self.user_author.following.count()
        self.assertEqual(follow_count, follow_count_after_unfollow)

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
