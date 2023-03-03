from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Post, User


class PostFollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user: User = User.objects.create_user(username='follow')
        cls.author: User = User.objects.create_user(username='author')

    def setUp(cls):
        cls.follow_client = Client()
        cls.follow_client.force_login(cls.user)
        cache.clear()

    def test_view_follow_unfollow(self):
        """*** FOLLOW: проверка создания/удаления подписки."""
        Follow.objects.all().delete()
        follow_num = Follow.objects.count()
        # Подпишемся
        response = self.follow_client.post(
            reverse('posts:profile_follow', args=(self.author.username,)),
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse('posts:profile', args=(self.author.username,)))
        # Проверяем, увеличилось ли число подписок
        self.assertEqual(Follow.objects.count(), follow_num + 1)
        follow = Follow.objects.first()
        self.assertEqual(follow.user, self.user)
        self.assertEqual(follow.author, self.author)

        # Отпишемся
        response = self.follow_client.post(
            reverse('posts:profile_unfollow', args=(self.author.username,)),
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse('posts:profile', args=(self.author.username,)))
        # Проверяем, увеличилось ли число подписок
        self.assertEqual(Follow.objects.count(), 0)

    def test_view_follow_index(self):
        """*** FOLLOW: проверка появления подписки в ленте."""
        Follow.objects.all().delete()
        Post.objects.all().delete()

        # Создадим запись поста в БД для проверки
        Post.objects.create(text='Тестовый текст поста', author=self.author)

        # Проверяем есть ли пост в ленте
        response = self.follow_client.get(
            reverse('posts:follow_index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['page_obj']), 0)

        # Подпишемся
        Follow.objects.create(user=self.user, author=self.author)
        # Проверяем есть ли пост в ленте
        response = self.follow_client.get(
            reverse('posts:follow_index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['page_obj']), 1)
