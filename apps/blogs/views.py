from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Q, F
from django.http import HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError
from .models import Blog, BlogStatus, CategoryChoices
from .forms import BlogForm, ContactForm

def blog_list(request):
    """
    Homepage view for INKSPACE.
    MVT Flow:
    1. Queries published blogs from the SQLite database.
    2. Separates featured article from latest stories.
    3. Handles category filtering and search queries.
    4. Passes context to 'blogs/blog_list.html'.
    """
    category_filter = request.GET.get('category', '').strip()
    search_query = request.GET.get('q', '').strip()

    published_blogs = Blog.objects.filter(status=BlogStatus.PUBLISHED).select_related('author')

    if category_filter and category_filter in CategoryChoices.values:
        published_blogs = published_blogs.filter(category=category_filter)

    if search_query:
        published_blogs = published_blogs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    # Pick featured post: either marked is_featured or the most recent published post
    featured_blog = published_blogs.filter(is_featured=True).first()
    if not featured_blog:
        featured_blog = published_blogs.first()

    # Remaining latest stories excluding the hero featured post
    if featured_blog:
        latest_stories = published_blogs.exclude(id=featured_blog.id)[:9]
    else:
        latest_stories = published_blogs[:9]

    context = {
        'featured_blog': featured_blog,
        'latest_stories': latest_stories,
        'categories': CategoryChoices.values,
        'current_category': category_filter,
        'search_query': search_query,
    }
    return render(request, 'blogs/blog_list.html', context)

def explore_blogs(request):
    """
    Explore page showing all published stories with category tabs and search.
    """
    category_filter = request.GET.get('category', '').strip()
    search_query = request.GET.get('q', '').strip()

    blogs = Blog.objects.filter(status=BlogStatus.PUBLISHED).select_related('author')

    if category_filter and category_filter in CategoryChoices.values:
        blogs = blogs.filter(category=category_filter)

    if search_query:
        blogs = blogs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(author__first_name__icontains=search_query) |
            Q(author__username__icontains=search_query)
        )

    context = {
        'blogs': blogs,
        'categories': CategoryChoices.values,
        'current_category': category_filter,
        'search_query': search_query,
    }
    return render(request, 'blogs/explore.html', context)

def blog_detail(request, slug):
    """
    Blog detail & reading view.
    MVT Flow:
    1. Fetches blog by unique slug.
    2. Enforces access control: Draft posts are only accessible by their author.
    3. Increments view count safely using F() expressions.
    4. Retrieves related stories from the same author.
    5. Renders 'blogs/blog_detail.html'.
    """
    blog = get_object_or_404(Blog.objects.select_related('author'), slug=slug)

    # Permission check for drafts
    if blog.status == BlogStatus.DRAFT:
        if not request.user.is_authenticated or request.user != blog.author:
            raise PermissionDenied("You do not have permission to view this unpublished draft.")

    # Increment view count
    Blog.objects.filter(pk=blog.pk).update(views_count=F('views_count') + 1)
    blog.refresh_from_db(fields=['views_count'])

    # Retrieve other posts by this author
    more_from_author = Blog.objects.filter(
        author=blog.author,
        status=BlogStatus.PUBLISHED
    ).exclude(id=blog.id)[:3]

    # Check relationship between logged-in reader and author
    is_author = request.user.is_authenticated and request.user == blog.author
    is_following = False

    if request.user.is_authenticated and not is_author:
        from apps.accounts.models import Follow
        is_following = Follow.objects.filter(follower=request.user, following=blog.author).exists()

    context = {
        'blog': blog,
        'more_from_author': more_from_author,
        'is_author': is_author,
        'is_following': is_following,
    }
    return render(request, 'blogs/blog_detail.html', context)

@login_required
def create_blog(request):
    """
    Create a new blog post.
    MVT Flow:
    1. Requires authenticated user (@login_required).
    2. GET renders empty BlogForm with AI Assistant widget ready.
    3. POST validates form inputs, attaches request.user as author.
    4. Saves to database and redirects to the new blog or My Blogs list.
    """
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = request.user

            # If the user clicked "Publish Blog" button specifically
            action = request.POST.get('action')
            if action == 'publish':
                blog.status = BlogStatus.PUBLISHED
            elif action == 'draft':
                blog.status = BlogStatus.DRAFT

            blog.save()
            messages.success(
                request,
                f"Your story '{blog.title}' has been successfully {blog.status.lower()}ed!"
            )
            if blog.status == BlogStatus.PUBLISHED:
                return redirect('blogs:blog_detail', slug=blog.slug)
            return redirect('blogs:my_blogs')
        else:
            messages.error(request, "Please check the form for errors.")
    else:
        form = BlogForm(initial={'status': BlogStatus.DRAFT})

    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, 'blogs/create_blog.html', context)

@login_required
def edit_blog(request, slug):
    """
    Edit an existing blog post.
    MVT Flow:
    1. Fetches blog by slug.
    2. Enforces owner authorization (only author can edit).
    3. Pre-populates form with existing instance data.
    4. Saves updates upon valid POST submission.
    """
    blog = get_object_or_404(Blog, slug=slug)

    # Authorization check
    if blog.author != request.user:
        raise PermissionDenied("You are not authorized to edit this story.")

    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            updated_blog = form.save(commit=False)
            action = request.POST.get('action')
            if action == 'publish':
                updated_blog.status = BlogStatus.PUBLISHED
            elif action == 'draft':
                updated_blog.status = BlogStatus.DRAFT
            updated_blog.save()

            messages.success(request, f"Changes saved for '{updated_blog.title}'.")
            if updated_blog.status == BlogStatus.PUBLISHED:
                return redirect('blogs:blog_detail', slug=updated_blog.slug)
            return redirect('blogs:my_blogs')
        else:
            messages.error(request, "Could not save changes. Please review the errors below.")
    else:
        form = BlogForm(instance=blog)

    context = {
        'form': form,
        'blog': blog,
        'is_edit': True,
    }
    return render(request, 'blogs/edit_blog.html', context)

@login_required
def delete_blog(request, slug):
    """
    Delete a blog post (POST only for security).
    MVT Flow:
    1. Checks owner authorization.
    2. Verifies request is POST (guards against CSRF / GET deletion).
    3. Deletes record from database.
    4. Redirects to My Blogs with confirmation message.
    """
    blog = get_object_or_404(Blog, slug=slug)

    if blog.author != request.user:
        raise PermissionDenied("You are not authorized to delete this story.")

    if request.method == 'POST':
        title = blog.title
        blog.delete()
        messages.success(request, f"Blog post '{title}' was permanently deleted.")
        return redirect('blogs:my_blogs')

    # If requested via GET, show confirmation warning or redirect back
    return redirect('blogs:my_blogs')

@login_required
def my_blogs(request):
    """
    User dashboard to manage personal blog posts.
    MVT Flow:
    1. Filters blogs by logged-in user (request.user).
    2. Computes counts for All, Published, and Draft tabs.
    3. Filters list based on active tab ('all', 'published', 'draft').
    4. Renders 'blogs/my_blogs.html'.
    """
    user_blogs = Blog.objects.filter(author=request.user)
    
    total_count = user_blogs.count()
    published_count = user_blogs.filter(status=BlogStatus.PUBLISHED).count()
    drafts_count = user_blogs.filter(status=BlogStatus.DRAFT).count()

    status_filter = request.GET.get('status', 'all').lower()

    if status_filter == 'published':
        filtered_blogs = user_blogs.filter(status=BlogStatus.PUBLISHED)
    elif status_filter == 'draft':
        filtered_blogs = user_blogs.filter(status=BlogStatus.DRAFT)
    else:
        filtered_blogs = user_blogs
        status_filter = 'all'

    context = {
        'blogs': filtered_blogs,
        'status_filter': status_filter,
        'total_count': total_count,
        'published_count': published_count,
        'drafts_count': drafts_count,
    }
    return render(request, 'blogs/my_blogs.html', context)

def about_view(request):
    """
    Renders the INKSPACE About page.
    """
    return render(request, 'blogs/about.html')

def contact_view(request):
    """
    Handles inquiries via the Contact form.
    Validates form data and returns success notification.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            # Message received successfully
            messages.success(
                request,
                f"Thank you, {name}! Your message regarding '{subject}' has been received. Our team will review and reply to {email} shortly."
            )
            return redirect('blogs:contact')
        else:
            messages.error(request, "Please correct the errors in the contact form.")
    else:
        form = ContactForm()

    return render(request, 'blogs/contact.html', {'form': form})

def privacy_view(request):
    """
    Renders the INKSPACE Privacy Policy page.
    """
    return render(request, 'blogs/privacy.html')

# Custom HTTP error views
def custom_403_view(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def custom_404_view(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def custom_500_view(request):
    return render(request, 'errors/500.html', status=500)

