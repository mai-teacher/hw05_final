from http import HTTPStatus

from django.core.cache import cache
from django.db import IntegrityError, transaction
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

    def test_follow(self):
        """*** FOLLOW: проверка создания подписки."""
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

    def test_unfollow(self):
        """*** FOLLOW: проверка удаления подписки."""
        Follow.objects.all().delete()
        # Подпишемся
        Follow.objects.create(user=self.user, author=self.author)
        # Проверяем, увеличилось ли число подписок
        self.assertEqual(Follow.objects.count(), 1)

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

    def test_follow_index(self):
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

    def test_self_follow(self):
        """*** FOLLOW: проверка ограничения на самоподписку."""
        Follow.objects.all().delete()
        # Подпишемся
        try:
            with transaction.atomic():
                Follow.objects.create(user=self.user, author=self.user)
        except IntegrityError:
            pass
        # Проверяем, увеличилось ли число подписок
        self.assertEqual(Follow.objects.count(), 0)

    def test_second_follow(self):
        """*** FOLLOW: проверка повторной подписки."""
        Follow.objects.all().delete()
        # Подпишемся
        Follow.objects.create(user=self.user, author=self.author)
        # Проверяем, увеличилось ли число подписок
        self.assertEqual(Follow.objects.count(), 1)
        try:
            with transaction.atomic():
                # Подпишемся повторно
                Follow.objects.create(user=self.user, author=self.author)
        except IntegrityError:
            pass
        # Проверяем, увеличилось ли число подписок
        self.assertEqual(Follow.objects.count(), 1)
