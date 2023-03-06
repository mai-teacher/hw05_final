from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user: User = User.objects.create_user(username='author')
        cls.user2: User = User.objects.create_user(username='non_author')
        # Создадим запись в БД для проверки доступности адреса group/test-slug/
        cls.group: Group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test-slug',
            description='Описание тестовой группы',
        )
        # Создадим запись в БД для проверки доступности адреса posts/1/
        cls.post: Post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group
        )
        cls.names_table = (
            ('posts:index', None,
             '/'),
            ('posts:group_list', (cls.group.slug,),
             f'/group/{cls.group.slug}/'),
            ('posts:profile', (cls.user.username,),
             f'/profile/{cls.user.username}/'),
            ('posts:post_detail', (cls.post.id,),
             f'/posts/{cls.post.id}/'),
            ('posts:post_edit', (cls.post.id,),
             f'/posts/{cls.post.id}/edit/'),
            ('posts:post_create', None,
             '/create/'),
            ('posts:add_comment', (cls.post.id,),
             f'/posts/{cls.post.id}/comment/'),
            ('posts:follow_index', None,
             '/follow/'),
            ('posts:profile_follow', (cls.user.username,),
             f'/profile/{cls.user.username}/follow/'),
            ('posts:profile_unfollow', (cls.user.username,),
             f'/profile/{cls.user.username}/unfollow/'),
        )

    def setUp(self):
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.client2 = Client()
        self.client2.force_login(self.user2)
        cache.clear()

    def test_urls_reverse_names(self):
        """*** URLS: Проверяем преобразование имен в url."""
        for name, arg, url in self.names_table:
            with self.subTest(url=url):
                self.assertEqual(reverse(name, args=arg), url)

    def test_urls_page404(self):
        """*** URLS: Проверяем несуществующую страницу."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_template_page404(self):
        """*** URLS: Проверяем шаблон страницы 404."""
        # Проверьте, что используется шаблон core/404.html
        response = self.client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_by_author(self):
        """*** URLS: Проверяем страницы URL доступны автору."""
        redirect_names = {
            'posts:add_comment': 'posts:post_detail',
            'posts:profile_follow': 'posts:profile',
        }
        for name, arg, _ in self.names_table:
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse(name, args=arg))
                if name == 'posts:profile_unfollow':
                    self.assertEqual(response.status_code,
                                     HTTPStatus.NOT_FOUND)
                elif name in redirect_names.keys():
                    self.assertRedirects(
                        response,
                        reverse(redirect_names.get(name), args=arg))
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_by_non_author(self):
        """*** URLS: Проверяем страницы URL доступны авторизир.пользователю."""
        redirect_names = {
            'posts:post_edit': 'posts:post_detail',
            'posts:add_comment': 'posts:post_detail',
            'posts:profile_follow': 'posts:profile',
            'posts:profile_unfollow': 'posts:profile',
        }
        for name, arg, _ in self.names_table:
            with self.subTest(name=name):
                response = self.client2.get(reverse(name, args=arg))
                if name in redirect_names.keys():
                    self.assertRedirects(
                        response,
                        reverse(redirect_names.get(name), args=arg))
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_by_guest(self):
        """*** URLS: Проверяем страницы URL доступны любому пользователю."""
        redirect_names = (
            'posts:post_edit',
            'posts:post_create',
            'posts:add_comment',
            'posts:follow_index',
            'posts:profile_follow',
            'posts:profile_unfollow',
        )
        login = reverse('login')
        for name, arg, _ in self.names_table:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=arg))
                if name in redirect_names:
                    reverse_name = reverse(name, args=arg)
                    self.assertRedirects(
                        response,
                        f'{login}?next={reverse_name}')
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """*** URLS: Проверяем URL-адрес использует соответствующий шаблон."""
        templates_table = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:group_list', (self.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (self.user.username,), 'posts/profile.html'),
            ('posts:post_detail', (self.post.id,), 'posts/post_detail.html'),
            ('posts:post_edit', (self.post.id,), 'posts/create_post.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:follow_index', None, 'posts/follow.html'),
        )
        for name, arg, template in templates_table:
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse(name, args=arg))
                self.assertTemplateUsed(response, template)
