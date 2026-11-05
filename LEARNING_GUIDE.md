# INKSPACE – Complete Django MVT & Gemini AI Learning Guide

Welcome to the **INKSPACE Learning Guide**. This document is designed as your master architectural companion to understand the internal mechanics of Django, the Model-View-Template (MVT) pattern, database operations, and external API integrations using real code from this project.

---

## Table of Contents
1. [Understanding the Django MVT Architecture](#1-understanding-the-django-mvt-architecture)
2. [Project Configuration (`config/`)](#2-project-configuration-config)
   - `settings.py`
   - `urls.py`
   - `wsgi.py` & `asgi.py`
3. [Apps Breakdown & Responsibilities](#3-apps-breakdown--responsibilities)
   - `apps/accounts/` (Authentication & Profiles)
   - `apps/blogs/` (Core CRUD & Reading Platform)
   - `apps/chatbot/` (Google Gemini AI Writing Assistant)
4. [Models & Database Internals](#4-models--database-internals)
   - `Blog` Model, Slug Generation, and Reading Time Calculation
   - `Profile` Model and Django Signals (`post_save`)
   - `AIGenerationLog` Audit Model
5. [Forms, ModelForms & Server-Side Validation](#5-forms-modelforms--server-side-validation)
   - `SignUpForm` and `LoginForm`
   - `BlogForm` ModelForm
6. [Views & Request Lifecycle Walkthrough](#6-views--request-lifecycle-walkthrough)
   - `blog_list()`
   - `blog_detail()`
   - `create_blog()`
   - `edit_blog()`
   - `delete_blog()`
   - `my_blogs()`
7. [Templates, Inheritance & Template Tags](#7-templates-inheritance--template-tags)
8. [Google Gemini AI Integration Deep Dive](#8-google-gemini-ai-integration-deep-dive)
   - Why `services.py`?
   - The Official `google-genai` Python SDK
   - JSON Generation Flow & Insertion into the Blog Editor
9. [Security, CSRF & Authorization Standards](#9-security-csrf--authorization-standards)
10. [Step-by-Step Testing & Verification Guide](#10-step-by-step-testing--verification-guide)

---

## 1. Understanding the Django MVT Architecture

In traditional software engineering, MVC stands for **Model-View-Controller**. Django implements a slightly refined version called **MVT** (**Model-View-Template**):

```
+-------------------------------------------------------------+
|                          BROWSER                            |
+-------------------------------------------------------------+
            │ (1) HTTP GET/POST Request
            ▼
+-------------------------------------------------------------+
|                         urls.py                             |
|  Matches URL pattern (e.g., path('create/', views.create)) |
+-------------------------------------------------------------+
            │ (2) Dispatches to target View function
            ▼
+-------------------------------------------------------------+
|                         views.py                            |
|  Controls business logic, checks authentication,            |
|  validates forms, queries database                          |
+-------------------------------------------------------------+
       │                      │                      │
       │ (3) Form Validations │ (4) ORM Queries      │ (6) Renders HTML
       ▼                      ▼                      ▼
+---------------+     +---------------+     +---------------+
|   forms.py    |     |   models.py   |     | template.html |
|  Validates    |     |  Interacts    |     |  Renders DTL  |
|  user input   |     |  with SQLite  |     |  to Browser   |
+---------------+     +---------------+     +---------------+
                              │
                              ▼
                      +---------------+
                      |   db.sqlite3  |
                      +---------------+
```

### Responsibility Matrix:
- **Model (`models.py`)**: Defines the data schema, constraints, indexes, database relationships, and table methods. You never write raw SQL.
- **View (`views.py`)**: The controller/handler. It receives an `HttpRequest`, interacts with models/forms, decides what data is needed, and returns an `HttpResponse`.
- **Template (`templates/*.html`)**: The presentation layer. Django Template Language (DTL) tags like `{% for %}` and `{{ variable }}` render clean HTML.

---

## 2. Project Configuration (`config/`)

### `config/settings.py`

#### What is this file?
The central brain of the entire Django project. It contains all runtime configurations, installed applications, database drivers, template paths, security middleware, and third-party API configurations.

#### Key Sections Explained:
1. **`INSTALLED_APPS`**:
   Registers our three custom modular apps alongside Django's core packages:
   ```python
   INSTALLED_APPS = [
       'django.contrib.admin',
       'django.contrib.auth',
       'django.contrib.contenttypes',
       'django.contrib.sessions',
       'django.contrib.messages',
       'django.contrib.staticfiles',

       # Custom modular INKSPACE apps
       'apps.accounts.apps.AccountsConfig',
       'apps.blogs.apps.BlogsConfig',
       'apps.chatbot.apps.ChatbotConfig',
   ]
   ```
   *Why modular?* By keeping each feature in `apps.<feature>`, we prevent a monolithic codebase and make testing clean.

2. **`TEMPLATES`**:
   Configured with `'DIRS': [BASE_DIR / 'templates']`, instructing Django to look for global templates (such as `base.html`, `navbar.html`, `footer.html`) in the root template directory while also loading app-level templates (`APP_DIRS: True`).

3. **`DATABASES`**:
   Points to the file-based relational SQLite engine:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.sqlite3',
           'NAME': BASE_DIR / 'db.sqlite3',
       }
   }
   ```

4. **`GEMINI_API_KEY` & `GEMINI_MODEL`**:
   Read from the environment using `python-dotenv`:
   ```python
   GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
   GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')
   ```
   *Never hardcode keys.* This prevents accidental leaks to public repositories.

---

## 3. Apps Breakdown & Responsibilities

### `apps/accounts/`
Responsible exclusively for:
- User signup and login with email or username.
- Profile storage (bio, author role, avatar).
- Auto-creation of `Profile` via Django `post_save` signal.

### `apps/blogs/`
Responsible exclusively for:
- Blog CRUD operations (Create, Read, Update, Delete).
- Published vs Draft status visibility.
- Auto-generating URL slugs (`slugify`).
- Computing reading time estimates.
- Search and category filtering.

### `apps/chatbot/`
Responsible exclusively for:
- Managing communication with Google Gemini API via `services.py`.
- Providing JSON API endpoints (`/chatbot/generate-blog/` and `/chatbot/chat/`).
- Storing audit records in `AIGenerationLog`.
- Rendering the floating AI writing assistant widget.

---

## 4. Models & Database Internals

### The `Blog` Model (`apps/blogs/models.py`)

```python
class Blog(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blogs')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    description = models.CharField(max_length=250)
    cover_image = models.ImageField(upload_to='blog_covers/', blank=True, null=True)
    category = models.CharField(max_length=50, choices=CategoryChoices.choices)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=BlogStatus.choices, default=BlogStatus.DRAFT)
    is_featured = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
```

#### How does `save()` generate unique slugs?
When saving a blog, we override the default `save()` method:
```python
def save(self, *args, **kwargs):
    if not self.slug:
        base_slug = slugify(self.title) or 'story'
        unique_slug = base_slug
        counter = 1
        while Blog.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
        self.slug = unique_slug

    if self.status == BlogStatus.PUBLISHED and not self.published_at:
        self.published_at = timezone.now()
    elif self.status == BlogStatus.DRAFT:
        self.published_at = None

    super().save(*args, **kwargs)
```
1. `slugify("A Weekend in the Western Ghats")` produces `a-weekend-in-the-western-ghats`.
2. If another post already used this slug, the `while` loop checks `Blog.objects.filter(...)` and generates `a-weekend-in-the-western-ghats-1`.
3. If the user publishes the draft, `published_at` is timestamped with the current UTC time.

#### How is `reading_time` calculated?
```python
@property
def reading_time(self):
    words = len(self.content.split())
    minutes = math.ceil(words / 200)
    return max(1, minutes)
```
Average adult reading speed is approximately 200 words per minute. Using `@property`, templates can simply invoke `{{ blog.reading_time }}` as if it were a model field!

### The `Follow` Model (`apps/accounts/models.py`)
To enable readers to follow authors while strictly preventing self-following and duplicates at the database level:

```python
class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_set')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers_set')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # 1. Prevent duplicate follows
            models.UniqueConstraint(fields=['follower', 'following'], name='unique_user_follow'),
            # 2. Prevent self-following at the database engine level
            models.CheckConstraint(
                condition=~models.Q(follower=models.F('following')),
                name='prevent_self_follow'
            ),
        ]

    def clean(self):
        if self.follower_id == self.following_id:
            raise ValidationError("An author cannot follow themselves.")
```

#### Multi-Layer Defense Against Self-Following
1. **Frontend / Template**: The Follow button is hidden completely whenever `request.user == blog.author`.
2. **View Logic**: `toggle_follow_view` checks `if request.user.id == target_author.id` and returns an error message or HTTP 400.
3. **Model Validation**: `clean()` prevents programmatic creation of invalid relationships.
4. **Database Constraint**: `CheckConstraint` enforces SQLite/Postgres rule preventing `follower_id == following_id`.

---

## 5. Forms, ModelForms & Server-Side Validation

### Why Django Forms?
Never rely on client-side HTML `<input required>` alone. Malicious actors or API clients can bypass HTML attributes. Django Forms sanitize input, check data types, enforce CSRF protection, and convert strings into Python objects.

### `ContactForm` (`apps/blogs/forms.py`)
```python
class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Your Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'your.email@example.com'}))
    subject = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Message Subject'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Write your message...'}))

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise ValidationError("Please provide a message of at least 10 characters.")
        return message
```

### `BlogForm` (`apps/blogs/forms.py`)
```python
class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['title', 'description', 'category', 'content', 'cover_image', 'status']

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise ValidationError("Blog title must be at least 5 characters long.")
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if len(description) < 15:
            raise ValidationError("Please provide a meaningful description of at least 15 characters.")
        if len(description) > 250:
            raise ValidationError("Description cannot exceed 250 characters.")
        return description
```

#### How does Django form validation execute?
1. User submits POST data.
2. `form = BlogForm(request.POST, request.FILES)` instantiates the form.
3. `form.is_valid()` executes:
   - Field-level cleaning (e.g., checks max length, required flags).
   - Method `clean_<field_name>()` on specific attributes.
   - Cross-field validation method `clean()`.
4. If errors are found, `form.errors` is populated and passed to the template.
5. If valid, `form.cleaned_data` contains sanitized, type-safe data.

---

## 6. Views & Request Lifecycle Walkthrough

### 1. `blog_list` View (Homepage)
```python
def blog_list(request):
    category_filter = request.GET.get('category', '').strip()
    search_query = request.GET.get('q', '').strip()

    published_blogs = Blog.objects.filter(status=BlogStatus.PUBLISHED).select_related('author')
    ...
```
**Why `select_related('author')`?**
Without `select_related`, accessing `{{ story.author.username }}` inside a loop generates a new SQL query for every card (the notorious $N+1$ query problem). `select_related('author')` performs an SQL `INNER JOIN` in a single query, keeping database latency negligible.

### 2. `create_blog` View
```python
@login_required
def create_blog(request):
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = request.user
            ...
            blog.save()
            return redirect('blogs:blog_detail', slug=blog.slug)
```
**Why `form.save(commit=False)`?**
The `author` field is required by the `Blog` model, but is not exposed in the HTML form to prevent users from spoofing the author. `commit=False` produces an unsaved model instance, allowing the view to securely set `blog.author = request.user` before writing to `db.sqlite3`.

### 3. `delete_blog` View (POST-Only Protection)
```python
@login_required
def delete_blog(request, slug):
    blog = get_object_or_404(Blog, slug=slug)
    if blog.author != request.user:
        raise PermissionDenied("You are not authorized to delete this story.")

    if request.method == 'POST':
        blog.delete()
        messages.success(request, f"Blog post '{blog.title}' was deleted.")
        return redirect('blogs:my_blogs')
    return redirect('blogs:my_blogs')
```
**Why POST-only deletion?**
If deletion was allowed via `GET /blogs/<slug>/delete/`, web crawlers, search indexing bots, or browser prefetching could accidentally delete articles! Enforcing `request.method == 'POST'` with CSRF tokens guarantees deletion is an intentional user action.

---

## 7. Templates, Inheritance & Template Tags

INKSPACE uses a master template pattern:
- **`templates/base.html`**: The skeleton containing `<head>`, Bootstrap CSS, Google Fonts, navbar, message alerts, floating chatbot widget, and footer.
- Child templates (e.g. `blog_detail.html`) extend `base.html`:
  ```html
  {% extends 'base.html' %}
  {% block title %}{{ blog.title }} – INKSPACE{% endblock %}
  {% block content %}
    <!-- Page specific HTML -->
  {% endblock %}
  ```

---

## 8. Google Gemini AI Integration Deep Dive

### Why `apps/chatbot/services.py`?
Separation of concerns is fundamental to clean architecture. Views should handle web requests, and models should manage data. All external API networking, SDK initialization, and prompt engineering lives in a dedicated service layer: `GeminiService`.

### The AI Writing Mentor & 5 Dedicated Modes
The assistant operates as a professional writing mentor with 5 dedicated writing modes:
1. **Mentor Mode (Default)**: Automatically unpacks simple topics (e.g., *"Need food topic"*) into 5 engaging titles, a short preview description, a structured content outline, target audience insight, and a prompt to develop into a full blog.
2. **Full Blog Mode (`full_blog`)**: Generates publishing-ready articles with title, description, and structured sections.
3. **Catchy Titles Mode (`titles`)**: Generates 5–7 compelling, high-converting blog titles with 1-line strategic rationales.
4. **Description Mode (`description`)**: Generates 2–3 concise, attractive short preview descriptions (< 200 chars).
5. **Content Ideas Mode (`ideas`)**: Recommends a structured content roadmap, key headings/subheadings, and target audience insights.
6. **Improve Writing Mode (`improve`)**: Rewrites and elevates user-supplied text with cleaner flow and active vocabulary, providing a bulleted breakdown of key improvements.

### Multi-turn Conversation Memory & Context Flow
In `GeminiService.chat_assist`, the conversation history is formatted into `google.genai.types.Content` objects:
```python
contents = []
for turn in history[-8:]:
    role = "user" if turn.get('role') == 'user' else "model"
    contents.append(types.Content(
        role=role,
        parts=[types.Part.from_text(text=turn.get('content'))]
    ))
contents.append(types.Content(
    role="user",
    parts=[types.Part.from_text(text=current_user_message)]
))
```
This enables conversational context flow: an author can say *"Travel in Kerala"*, receive 5 title options, reply *"I like title #2"*, and then command *"Generate the full blog"*—and Gemini understands the entire context thread!

### Input Box & Scrollbar Fix
To prevent unwanted vertical scrollbars and handle multiline input smoothly:
- **CSS**: The textarea is constrained with `min-height: 42px; max-height: 120px; overflow-y: hidden; resize: none;`.
- **JavaScript**: Dynamically recalculates `scrollHeight` on the `input` event, expanding smoothly up to 120px, and enables `.has-scroll` with a custom thin scrollbar only when maximum height is exceeded.
- **Keyboard Navigation**: Pressing `Enter` submits the form, while `Shift + Enter` inserts a newline.

### Inserting Content into the Blog Editor
In `chatbot.js`, generated titles, descriptions, and full articles feature one-click action buttons:
```javascript
document.getElementById('id_title').value = parsedData.title;
document.getElementById('id_description').value = parsedData.description;
document.getElementById('id_content').value = parsedData.content;
```
If the author is on any other page, the content is copied to the clipboard with a prompt directing them to the blog creation page. Content is never automatically saved or published without the author's explicit review.

---

## 9. Security, CSRF & Authorization Standards

1. **CSRF (Cross-Site Request Forgery)**:
   Every HTML `<form>` includes `{% csrf_token %}`. Django issues a cryptographically secure token checked on every POST submission.
2. **Owner-Only Authorization**:
   In `edit_blog` and `delete_blog`:
   ```python
   if blog.author != request.user:
       raise PermissionDenied()
   ```
   If a user crafts a URL for someone else's blog slug, Django immediately returns an HTTP 403 Forbidden status and renders `templates/errors/403.html`.
3. **Safe Queries & SQL Injection Prevention**:
   Django ORM uses parameterized queries (`Q` objects and filter keywords). User strings are never concatenated directly into SQL queries.

---

## 10. Step-by-Step Testing & Verification Guide

Run the built-in test suite:
```bash
python manage.py test apps.accounts
python manage.py test apps.blogs
python manage.py test apps.chatbot
```

### Manual Verification Checklist:
1. **Authentication**: Register a new user at `/accounts/signup/`. Verify redirection and avatar display in navbar.
2. **Story Creation**: Navigate to `/create/`, click "Generate with AI", enter "Benefits of Learning Python", and verify title/description/content generation.
3. **Editor Insertion**: Click "Use Generated Content in Editor" and verify all fields populate.
4. **Draft vs Published**: Save as Draft. Verify it appears on `/my-blogs/` with a yellow "Draft" pill, and is hidden from the public homepage.
5. **Editing**: Edit the post, change status to "Publish Now", and confirm it appears on the homepage and explore feed.
