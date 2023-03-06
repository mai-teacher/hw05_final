from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post, User

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user: User = User.objects.create_user(username='author')
        cls.group: Group = Group.objects.create(
            title='Группа-1',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2: Group = Group.objects.create(
            title='Группа-2',
            slug='test-slug2',
            description='Тестовое описание группы 2',
        )
        cls.post: Post = Post.objects.create(
            text='Пост для редактирования',
            author=cls.user,
            group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание/удаление/копирование/перемещение/изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_forms_by_guest(self):
        """*** FORMS: проверка создания нового поста."""
        posts_count = Post.objects.count()
        response = self.client.post(
            reverse('posts:post_create'),
            data={'text': 'by Guest'},
            follow=True
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверяем, сработал ли редирект
        url = f"{reverse('login')}?next={reverse('posts:post_create')}"
        self.assertRedirects(response, url)

    def test_forms_create_post(self):
        """*** FORMS: проверка создания нового поста."""
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
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
            'text': 'Новый пост',
            'group': self.group.id,
            'image': uploaded,
        }
        Post.objects.all().delete()
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse('posts:profile', args=(self.user.username,)))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        new_post = Post.objects.first()
        # Проверяем новый пост
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.group.id, form_data['group'])
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.image.name,
                         'posts/' + form_data['image'].name)

    def test_forms_edit_post(self):
        """*** FORMS: проверка редактирования поста."""
        form_data = {
            'text': 'Отредактированный пост',
            'group': self.group2.id,
        }
        posts_count = Post.objects.count()
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse('posts:post_detail', args=(self.post.id,)))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)
        post = Post.objects.first()
        # Проверяем, изменилось ли id
        self.assertEqual(post.id, self.post.id)
        # Проверяем, изменился ли author
        self.assertEqual(post.author, self.post.author)
        # Проверяем изменение текста
        self.assertEqual(post.text, form_data['text'])
        # Проверяем изменение группы
        self.assertEqual(post.group.id, form_data['group'])

        response = self.authorized_client.get(
            reverse('posts:group_list', args=(post.group.slug,)))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_add_comments(self):
        """*** FORMS: проверка добавления комментария."""
        Comment.objects.all().delete()
        post = Post.objects.first()
        form_data = {
            'text': 'Добавление нового комментария',
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(post.id,)),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse('posts:post_detail', args=(self.post.id,)))
        # Проверяем, увеличилось ли число комментарий
        self.assertEqual(Comment.objects.count(), 1)
        context = Comment.objects.first()
        self.assertEqual(context.text, form_data['text'])
        self.assertEqual(context.author, self.user)
        # Проверяем, изменилось ли id поста
        self.assertEqual(post.id, self.post.id)
        # Проверяем, изменился ли author поста
        self.assertEqual(post.author, self.post.author)
        # Проверяем изменение текста поста
        self.assertEqual(post.text, self.post.text)

    def test_anonym_add_comments(self):
        """*** FORMS: проверка добавления комментария анонимом."""
        post = Post.objects.first()
        form_data = {
            'text': 'Добавление нового комментария',
        }
        # Отправляем POST-запрос
        reverse_name_add = reverse('posts:add_comment', args=(post.id,))
        response = self.client.post(
            reverse_name_add,
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект на login
        login = reverse('login')
        self.assertRedirects(response, f'{login}?next={reverse_name_add}')
