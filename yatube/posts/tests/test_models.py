from django.test import TestCase

from posts.models import Group, Post, User

TEST_STR_CHAR = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user: User = User.objects.create_user(username='author')
        cls.group: Group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post: Post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦ',
        )

    def test_models_have_correct_object_names(self):
        """*** MODEL: Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(str(self.group), self.group.title)
        self.assertEqual(str(self.post), self.post.text[:TEST_STR_CHAR])

    def test_models_verbose_name(self):
        """*** MODEL: Проверяем verbose_name моделей совпадают с ожидаемыми."""
        post_field_verbose = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка',
        }
        group_field_verbose = {
            'title': 'Название группы',
            'slug': 'Адрес',
            'description': 'Описание группы',
        }
        field_verbose_list = (
            (self.post, post_field_verbose),
            (self.group, group_field_verbose)
        )
        for model, field_verbose in field_verbose_list:
            for field, name in field_verbose.items():
                with self.subTest(field=field):
                    self.assertEqual(model._meta.get_field(field).verbose_name,
                                     name)

    def test_models_help_text(self):
        """*** MODEL: Проверяем help_text моделей совпадают с ожидаемыми."""
        self.assertEqual(self.post._meta.get_field('text').help_text,
                         'Введите текст поста')
        self.assertEqual(self.post._meta.get_field('group').help_text,
                         'Выберите группу')
