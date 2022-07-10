from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_empty = Group.objects.create(
            title='Пустая группа',
            slug='test_slug_empty_group'
        )
        cls.post = Post.objects.create(
            author=PostViewTests.user,
            text='Тестовый пост',
            id='1',
            group=PostViewTests.group,
        )

        cls.posts_pages_reverse = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={
                    'username': PostViewTests.user.username}),
        ]

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = User.objects.create_user(username='author')
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        test_post = Post.objects.create(
            author=self.user,
            text='Тестовый пост авторизованного юзера'
        )
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.author.username}):
                        'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': test_post.pk}):
                        'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': test_post.pk}):
                        'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Шаблон index/group/profile сформирован с правильным контекстом."""
        for reverse_name in self.posts_pages_reverse:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post = response.context['page_obj'][0]
                text = post.text
                author_username = post.author.username
                group_title = post.group.title
                group_description = post.group.description
                self.assertEqual(text, self.post.text)
                self.assertEqual(author_username, PostViewTests.user.username)
                self.assertEqual(group_title, self.post.group.title)
                self.assertEqual(group_description,
                                 self.post.group.description)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'}))
        self.assertEqual(response.context.get('post').text, self.post.text)

    def test_group_list_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}))
        self.assertEqual(response.context.get('group').title, self.group.title)
        self.assertEqual(response.context.get('group').slug, self.group.slug)

    def test_post_show_in_correct_pages(self):
        """ Пост отображается на главной странице и на странице группы,
        указанной при создании, не отображатеся в другой группе."""
        for reverse_name in self.posts_pages_reverse:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post = response.context['page_obj'][0]
                text = post.text
                author_username = post.author.username
                group_title = post.group.title
                self.assertEqual(text, self.post.text)
                self.assertEqual(author_username, PostViewTests.user.username)
                self.assertEqual(group_title, self.post.group.title)
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug_empty_group'}))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        test_post = Post.objects.create(
            author=self.user,
            text='Тестовый пост авторизованного юзера'
        )
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': test_post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertTrue(response.context.get('is_edit'))


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth1')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test_slug2',
            description='Описание')
        cls.posts = []
        for i in range(1, 14):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        test_cases = [
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.author.username}),
            reverse('posts:group_list',
                    kwargs={'slug': PaginatorViewsTest.group.slug}),
            reverse('posts:index'),
        ]
        for expected in test_cases:
            with self.subTest(expected=expected):
                response = self.client.get(expected)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_pages_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        test_cases = [
            reverse('posts:profile', kwargs={'username':
                    PaginatorViewsTest.author.username}) + '?page=2',
            reverse('posts:group_list',
                    kwargs={'slug':
                            PaginatorViewsTest.group.slug}) + '?page=2',
            reverse('posts:index') + '?page=2',
        ]
        for expected in test_cases:
            with self.subTest(expected=expected):
                response = self.client.get(expected)
                self.assertEqual(len(response.context['page_obj']), 3)
