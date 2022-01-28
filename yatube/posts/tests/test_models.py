from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа'
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        text_post = post.text
        self.assertEqual(str(post), text_post[:15])

        group = PostModelTest.group
        group_title = group.title
        self.assertEqual(str(group), group_title)

    def test_verbose_name(self):
        """Проверяем, что поля имеют заданные verbose_name"""
        post = PostModelTest.post
        fields_verbose = {
            'group': 'Группа',
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'image': 'Изображение'
        }
        for field, expected_value in fields_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        """Проверяем, что поля имеют заданные help_text'ы"""
        post = PostModelTest.post
        fields_help_text = {
            'group': 'Выберите группу',
            'text': 'Введите текст поста'
        }
        for field, expected_value in fields_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )
