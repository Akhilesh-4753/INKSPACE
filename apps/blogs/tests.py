from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Blog, BlogStatus, CategoryChoices

class BlogTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='author1',
            email='author1@example.com',
            password='Password123!',
            first_name='Akhilesh',
            last_name='P'
        )
        self.other_user = User.objects.create_user(
            username='author2',
            email='author2@example.com',
            password='Password123!'
        )
        self.blog = Blog.objects.create(
            author=self.user,
            title='A Weekend in the Western Ghats',
            description='A short escape to the misty hills of Kerala.',
            category=CategoryChoices.TRAVEL,
            content='Full content about the nature and peaceful hills of Kerala.',
            status=BlogStatus.PUBLISHED,
            is_featured=True
        )

    def test_homepage_status_code(self):
        response = self.client.get(reverse('blogs:blog_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A Weekend in the Western Ghats')

    def test_blog_detail_accessible(self):
        response = self.client.get(reverse('blogs:blog_detail', kwargs={'slug': self.blog.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A Weekend in the Western Ghats')

    def test_draft_inaccessible_by_stranger(self):
        draft = Blog.objects.create(
            author=self.user,
            title='Secret Draft Story',
            description='Private draft summary.',
            content='Only author can read this draft.',
            status=BlogStatus.DRAFT
        )
        response = self.client.get(reverse('blogs:blog_detail', kwargs={'slug': draft.slug}))
        self.assertEqual(response.status_code, 403)

    def test_create_blog_requires_login(self):
        response = self.client.get(reverse('blogs:create_blog'))
        self.assertEqual(response.status_code, 302)

    def test_owner_can_delete_blog(self):
        self.client.login(username='author1', password='Password123!')
        response = self.client.post(reverse('blogs:delete_blog', kwargs={'slug': self.blog.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Blog.objects.filter(pk=self.blog.pk).exists())
