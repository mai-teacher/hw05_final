from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.forms import PostForm
from posts.models import Follow, Group, Post, User

TEST_POSTS_NUM = 13


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user: User = User.objects.create_user(username='author')
        # Создадим запись группы в БД для проверки
        cls.group: Group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test-slug',
            description='Описание тестовой группы',
        )
        # Создадим запись поста в БД для проверки
        cls.post: Post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group,
            # image='posts/cat.jpg'
        )

    def setUp(self):
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def get_page_context(self, response, is_detail=False):
        """ Проверяем словарь контекста страниц. """
        if is_detail:
            context = response.context['post']
        else:
            context = response.context['page_obj'][0]
        self.assertEqual(context.text, self.post.text)
        self.assertEqual(context.pub_date, self.post.pub_date)
        self.assertEqual(context.author, self.post.author)
        self.assertEqual(context.group, self.post.group)
        self.assertEqual(context.image, self.post.image)

    def test_view_context_index_page(self):
        """*** VIEWS: Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.get_page_context(response)

    def test_view_context_group_list_page(self):
        """*** VIEWS: Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,)))
        self.get_page_context(response)
        self.assertEqual(response.context['group'], self.group)

    def test_view_context_profile_page(self):
        """*** VIEWS: Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', args=(self.user.username,)))
        self.get_page_context(response)
        self.assertEqual(response.context['author'], self.user)

    def test_view_context_post_detail_page(self):
        """*** VIEWS: Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post.id,)))
        self.get_page_context(response, True)
        # TODO: context COMMENTS?!

    def test_view_context_post_create_edit_page(self):
        """*** VIEWS: Шаблоны post_create/post_edit сформированы правильно."""
        address = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,)),
        )
        form_fields = (
            ('text', forms.fields.CharField),
            ('group', forms.fields.ChoiceField),
            ('image', forms.fields.ImageField)
        )

        for addr_name, addr_arg in address:
            with self.subTest(addr_name=addr_name):
                response = self.authorized_client.get(
                    reverse(addr_name, args=addr_arg))
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)
                fields = response.context['form'].fields
                # Проверяет, что поле формы является экз-ом указанного класса
                for f_name, f_class in form_fields:
                    with self.subTest(f_name=f_name):
                        self.assertIsInstance(fields[f_name], f_class)

    def test_view_paginator(self):
        """*** VIEWS: проверка паджинаторов."""
        user2: User = User.objects.create_user(username='author2')
        address = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (user2.username,)),
            ('posts:follow_index', None),
        )
        pages = (
            ('?page=1', settings.POSTS_NUM),
            ('?page=2', TEST_POSTS_NUM - settings.POSTS_NUM),
        )
        # Удалим все посты из БД
        Post.objects.all().delete()
        # Создадим записи постов в БД для проверки
        post_list = [
            Post(
                text='Тестовый текст поста',
                author=user2,
                group=self.group
            )
            for _ in range(TEST_POSTS_NUM)
        ]
        Post.objects.bulk_create(post_list)

        # Подпишемся
        Follow.objects.all().delete()
        Follow.objects.create(user=self.user, author=user2)

        for addr_name, addr_arg in address:
            with self.subTest(addr_name=addr_name):
                for page_n, num in pages:
                    with self.subTest(page_n=page_n):
                        response = self.authorized_client.get(
                            reverse(addr_name, args=addr_arg)
                            + page_n)
                        self.assertEqual(len(response.context['page_obj']),
                                         num)

    def test_view_post_not_in_group2(self):
        """"*** VIEWS: пост не попал в группу2"""
        group2 = Group.objects.create(
            title='Пустая группа',
            slug='empty',
            description='Описание пустой группы',
        )
        response = self.client.get(
            reverse('posts:group_list', args=(group2.slug,)))
        self.assertEqual(len(response.context['page_obj']), 0)

        post = Post.objects.first()
        self.assertNotEqual(post.group, group2)
        # Проверка: группа2 должна быть пустой.
        self.assertEqual(group2.posts.count(), 0)
