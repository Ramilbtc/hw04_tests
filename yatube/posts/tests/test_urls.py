from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            id='1',
        )
        cls.url_names_auth = {
            '/': 'posts/index.html',
            '/group/slug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
        }
        cls.url_names_auth_user = {
            '/': 'posts/index.html',
            '/group/slug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
        }
        cls.url_names_not_auth = {
            '/': 'posts/index.html',
            '/group/slug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = User.objects.create_user(username='author')
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_pages_url_exists_at_desired_location_not_auth(self):
        """Страницы /posts/ доступные любому пользователю."""
        for address, template in StaticURLTests.url_names_not_auth.items():
            with self.subTest(address=address,
                              template=template):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_url_exists_at_desired_location_auth(self):
        """Страницы /posts/ доступные авторизированному пользователю."""
        for address, template in StaticURLTests.url_names_auth_user.items():
            with self.subTest(address=address, template=template):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_detail_url_exists_at_desired_location_authorized(self):
        """Страница /post_edit/ доступна автору поста."""
        if self.authorized_author == self.user:
            response = self.author.get('/posts/1/edit/')
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_edit_list_url_redirect_anonymous(self):
        """Страница /post_edit/ перенаправляет анонимного пользователя."""
        response = self.guest_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/edit/'
        )

    def test_create_url_redirect_anonymous(self):
        """Страница /create/ перенаправляет анонимного пользователя."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_urls_uses_correct_template_auth(self):
        """URL-адрес использует соответствующий шаблон/авторизованный."""
        if self.authorized_author == self.user:
            for address, template in StaticURLTests.url_names_auth.items():
                with self.subTest(address=address):
                    response = self.authorized_author.get(address)
                    self.assertTemplateUsed(response, template)
        for address, template in StaticURLTests.url_names_auth_user.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_not_auth(self):
        """URL-адрес использует соответствующий шаблон/неавторизованный."""
        for address, template in StaticURLTests.url_names_not_auth.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page_added_url_exists_at_desired_location(self):
        """Страница /unexisting_page/ доступна любому пользователю."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
