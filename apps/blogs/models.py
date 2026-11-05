import math
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone

class CategoryChoices(models.TextChoices):
    TRAVEL = 'Travel', 'Travel'
    TECHNOLOGY = 'Technology', 'Technology'
    LIFESTYLE = 'Lifestyle', 'Lifestyle'
    FOOD = 'Food', 'Food'
    EDUCATION = 'Education', 'Education'
    HEALTH = 'Health', 'Health'

class BlogStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    PUBLISHED = 'Published', 'Published'

class Blog(models.Model):
    """
    Blog article model for INKSPACE platform.
    Represents blog posts created by registered users with status, category,
    cover image, automatic slugs, and publication timestamps.
    """
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blogs',
        help_text="The author who created this blog post."
    )
    title = models.CharField(
        max_length=255,
        help_text="Catchy title for your blog post."
    )
    slug = models.SlugField(
        max_length=300,
        unique=True,
        blank=True,
        help_text="URL-friendly identifier generated from the title."
    )
    description = models.CharField(
        max_length=250,
        help_text="Short summary (max 250 characters) displayed on cards and search results."
    )
    cover_image = models.ImageField(
        upload_to='blog_covers/',
        blank=True,
        null=True,
        help_text="Cover image for the article header and feed previews."
    )
    category = models.CharField(
        max_length=50,
        choices=CategoryChoices.choices,
        default=CategoryChoices.TECHNOLOGY,
        help_text="Category topic that best fits this post."
    )
    content = models.TextField(
        help_text="Main article content in HTML or formatted text."
    )
    status = models.CharField(
        max_length=20,
        choices=BlogStatus.choices,
        default=BlogStatus.DRAFT,
        help_text="Publication status: Draft is private, Published is visible to everyone."
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether this post is featured on the homepage hero."
    )
    views_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of views this article has received."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the blog post was first created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when the blog post was last modified."
    )
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp when the post was changed to Published status."
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Blog Article'
        verbose_name_plural = 'Blog Articles'

    def __str__(self):
        return f"{self.title} by {self.author.username} ({self.status})"

    def save(self, *args, **kwargs):
        """
        Auto-generate unique slug from title on initial save or when title changes.
        Set published_at timestamp when status transitions to Published.
        """
        if not self.slug:
            base_slug = slugify(self.title) or 'story'
            unique_slug = base_slug
            counter = 1
            while Blog.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug

        # Manage publication date
        if self.status == BlogStatus.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        elif self.status == BlogStatus.DRAFT:
            self.published_at = None

        super().save(*args, **kwargs)

    @property
    def reading_time(self):
        """
        Estimate reading time based on an average reading speed of 200 words per minute.
        """
        words = len(self.content.split())
        minutes = math.ceil(words / 200)
        return max(1, minutes)

    @property
    def get_cover_image_url(self):
        """
        Return the proper URL for the blog cover image.
        Supports both local uploaded files in /media/ and external URLs (e.g. Unsplash),
        with an elegant editorial fallback.
        """
        if not self.cover_image:
            return "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80"
        val = str(self.cover_image).strip()
        if val.startswith("http://") or val.startswith("https://"):
            return val
        try:
            return self.cover_image.url
        except Exception:
            return "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80"
