from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Catchy title for your blog post.', max_length=255)),
                ('slug', models.SlugField(blank=True, help_text='URL-friendly identifier generated from the title.', max_length=300, unique=True)),
                ('description', models.CharField(help_text='Short summary (max 250 characters) displayed on cards and search results.', max_length=250)),
                ('cover_image', models.ImageField(blank=True, help_text='Cover image for the article header and feed previews.', null=True, upload_to='blog_covers/')),
                ('category', models.CharField(choices=[('Travel', 'Travel'), ('Technology', 'Technology'), ('Lifestyle', 'Lifestyle'), ('Food', 'Food'), ('Education', 'Education'), ('Health', 'Health')], default='Technology', help_text='Category topic that best fits this post.', max_length=50)),
                ('content', models.TextField(help_text='Main article content in HTML or formatted text.')),
                ('status', models.CharField(choices=[('Draft', 'Draft'), ('Published', 'Published')], default='Draft', help_text='Publication status: Draft is private, Published is visible to everyone.', max_length=20)),
                ('is_featured', models.BooleanField(default=False, help_text='Whether this post is featured on the homepage hero.')),
                ('views_count', models.PositiveIntegerField(default=0, help_text='Total number of views this article has received.')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Date and time when the blog post was first created.')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date and time when the blog post was last modified.')),
                ('published_at', models.DateTimeField(blank=True, help_text='Timestamp when the post was changed to Published status.', null=True)),
                ('author', models.ForeignKey(help_text='The author who created this blog post.', on_delete=django.db.models.deletion.CASCADE, related_name='blogs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Blog Article',
                'verbose_name_plural': 'Blog Articles',
                'ordering': ['-created_at'],
            },
        ),
    ]
