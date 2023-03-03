from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, User


class PostCacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user: User = User.objects.create_user(username='author')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_cache_index(self):
        Post.objects.create(text='Тестовый текст поста', author=self.user)
        response_before = self.authorized_client.get(reverse('posts:index'))
        Post.objects.all().delete()
        response_cache = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_before.content, response_cache.content)
        cache.clear()
        response_after = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_before.content, response_after.content)
