from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Blog, BlogStatus, CategoryChoices
from .forms import BlogForm

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

    def test_blog_form_sanitizes_script_tags(self):
        """Rich-text editor form must strip malicious <script> tags."""
        data = {
            'title': 'Test Sanitization Post',
            'description': 'Testing server side HTML sanitization with Bleach.',
            'category': 'Technology',
            'content': '<script>alert("hack")</script><h2>Introduction</h2><p>This is safe content with enough characters to pass validation.</p>',
            'status': 'Draft'
        }
        form = BlogForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        cleaned_content = form.cleaned_data['content']
        self.assertNotIn('<script>', cleaned_content)
        self.assertIn('<h2>Introduction</h2>', cleaned_content)
        self.assertIn('This is safe content', cleaned_content)

    def test_blog_form_preserves_safe_editor_tags(self):
        """Rich-text formatting like bold, lists, quotes, and links must be preserved."""
        data = {
            'title': 'Rich Formatting Test',
            'description': 'Verifying headings, lists, quotes, and links remain intact.',
            'category': 'Education',
            'content': '<h3>Section 1</h3><p><strong>Bold idea</strong> and <em>italic point</em>.</p>'
                       '<blockquote>Wise quote here.</blockquote>'
                       '<ul><li>Item 1</li><li>Item 2</li></ul>'
                       '<p><a href="https://example.com" target="_blank" rel="noopener noreferrer">External Link</a></p>',
            'status': 'Published'
        }
        form = BlogForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        cleaned = form.cleaned_data['content']
        self.assertIn('<h3>Section 1</h3>', cleaned)
        self.assertIn('<strong>Bold idea</strong>', cleaned)
        self.assertIn('<em>italic point</em>', cleaned)
        self.assertIn('<blockquote>Wise quote here.</blockquote>', cleaned)
        self.assertIn('<ul><li>Item 1</li><li>Item 2</li></ul>', cleaned)
        self.assertIn('href="https://example.com"', cleaned)

    def test_blog_form_strips_javascript_links(self):
        """Disallowed protocols like javascript: must be stripped for security."""
        data = {
            'title': 'XSS Attack Prevention',
            'description': 'Verifying javascript: URI scheme is blocked.',
            'category': 'Technology',
            'content': '<p>Check this <a href="javascript:alert(\'xss\')" onclick="evil()">Click Me</a> for a demonstration.</p>',
            'status': 'Draft'
        }
        form = BlogForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        cleaned = form.cleaned_data['content']
        self.assertNotIn('javascript:', cleaned)
        self.assertNotIn('onclick', cleaned)
        self.assertIn('Click Me', cleaned)

    def test_blog_form_validates_minimum_plain_text(self):
        """Empty HTML tags like <p><br></p> must not bypass length checks."""
        data = {
            'title': 'Empty Post Test',
            'description': 'Valid description with sufficient length here.',
            'category': 'Lifestyle',
            'content': '<p><br></p><div><br></div>',
            'status': 'Draft'
        }
        form = BlogForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)

    def test_blog_without_cover_image_returns_none_url(self):
        """A blog without a cover image should return None instead of an automatic default."""
        blog_no_cover = Blog.objects.create(
            author=self.user,
            title='No Cover Story',
            description='This story has no cover image.',
            category=CategoryChoices.TECHNOLOGY,
            content='This is a story created without uploading an image.',
            status=BlogStatus.PUBLISHED
        )
        self.assertIsNone(blog_no_cover.get_cover_image_url)
        self.assertFalse(blog_no_cover.has_cover_image)

    def test_create_blog_without_cover_image_succeeds(self):
        """Users must be able to create a blog without uploading a cover image."""
        self.client.login(username='author1', password='Password123!')
        response = self.client.post(reverse('blogs:create_blog'), {
            'title': 'Blog Created Without Cover',
            'description': 'Valid description with more than 15 characters.',
            'category': 'Education',
            'content': '<p>This is complete blog content without an uploaded cover image.</p>',
            'status': 'Published',
            'action': 'publish'
        })
        self.assertEqual(response.status_code, 302)
        new_blog = Blog.objects.get(title='Blog Created Without Cover')
        self.assertFalse(bool(new_blog.cover_image))
        self.assertIsNone(new_blog.get_cover_image_url)

    def test_my_blogs_vertical_card_view(self):
        """My Blogs page renders vertical card list with View, Edit, and Delete actions."""
        self.client.login(username='author1', password='Password123!')
        response = self.client.get(reverse('blogs:my_blogs'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A Weekend in the Western Ghats')
        self.assertContains(response, 'View')
        self.assertContains(response, 'Edit')
        self.assertContains(response, 'Delete')
        self.assertContains(response, 'myBlogsCardList')
        self.assertContains(response, 'All')
        self.assertContains(response, 'Published')
        self.assertContains(response, 'Drafts')

    def test_edit_blog_remove_cover_image(self):
        """Authors can remove an existing cover image during edit."""
        self.client.login(username='author1', password='Password123!')
        self.blog.cover_image = 'blog_covers/test_cover.jpg'
        self.blog.save()

        response = self.client.post(reverse('blogs:edit_blog', kwargs={'slug': self.blog.slug}), {
            'title': self.blog.title,
            'description': self.blog.description,
            'category': self.blog.category,
            'content': '<p>Updated content with enough length to pass validation.</p>',
            'status': self.blog.status,
            'remove_cover_image': '1',
            'action': 'publish'
        })
        self.assertEqual(response.status_code, 302)
        self.blog.refresh_from_db()
        self.assertFalse(bool(self.blog.cover_image))
        self.assertIsNone(self.blog.get_cover_image_url)
