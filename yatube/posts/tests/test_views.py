from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from posts.models import Post, Group

User = get_user_model()


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_author = User.objects.create_user(username='UserAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
            id='1',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (
                reverse('posts:group_list', kwargs={'slug': 'test-slug'})
            ): 'posts/group_list.html',
            (
                reverse('posts:profile', kwargs={'username': 'auth'})
            ): 'posts/profile.html',
            (
                reverse('posts:post_detail', kwargs={'post_id': '1'})
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            (
                reverse('posts:post_edit', kwargs={'post_id': '1'})
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.text
        self.assertEqual(task_text_0, 'Тестовая пост')
        self.assertEqual(first_object.pub_date, self.post.pub_date)
        self.assertEqual(first_object.author.username, 'auth')
        self.assertEqual(first_object.group.title, 'Тестовая группа')

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        self.assertEqual(
            response.context.get('group').title, 'Тестовая группа'
        )
        self.assertEqual(response.context.get('group').slug, 'test-slug')

    def test_group_list_page_no_another_post_show_correct_context(self):
        """Шаблон group_list не содержит поста с другой группой."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug2'})
        )
        self.assertNotIn('Тестовая пост', response.context['page_obj'])

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        self.assertIn('author', response.context)
        self.assertEqual(response.context.get('author').username, 'auth')

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertIn('post', response.context)
        self.assertEqual(response.context.get('post').text, 'Тестовая пост')

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_edit_show_correct_context(self):
        """Шаблон create_post для редактирования сформирован
        с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(('posts:post_edit'), kwargs={'post_id': '1'})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_author = User.objects.create_user(username='UserAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        Post.objects.bulk_create([Post(
            text=f"Текст тестового поста № {i}",
            author=cls.user_author,
            group=cls.group
        ) for i in range(13)])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_first_page_contains_ten_records(self):
        """Проверка работы паджинатора."""
        pages_with_paginator = {
            (reverse('posts:index')): 10,
            (reverse('posts:index') + '?page=2'): 3,
            (reverse('posts:group_list', kwargs={'slug': 'test-slug'})): 10,
            (
                reverse(
                    'posts:group_list', kwargs={'slug': 'test-slug'}
                ) + '?page=2'
            ): 3,
            (reverse('posts:profile', kwargs={'username': 'UserAuthor'})): 10,
            (
                reverse(
                    'posts:profile', kwargs={'username': 'UserAuthor'}
                ) + '?page=2'
            ): 3,
        }
        for reverse_name, post_on_page in pages_with_paginator.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), post_on_page
                )