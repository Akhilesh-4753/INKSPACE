# INKSPACE – Django MVT Blogging Platform with Google Gemini AI

**INKSPACE** is a responsive, Medium-inspired editorial blogging platform built with **Python**, **Django MVT architecture**, **SQLite 3**, and **Google Gemini AI** (`gemini-2.5-flash` / `gemini-3.8-flash` via the official `google-genai` Python SDK).

The project is designed with a strict Model-View-Template (MVT) pattern, providing an end-to-end learning codebase for Django developers to understand URL routing, views, models, templates, authentication, database operations, CRUD functionality, follow relationships, and AI integration.

---

## 🌟 Key Features

1. **Complete Django MVT Architecture**:
   - Clean modular app separation: `apps.accounts`, `apps.blogs`, and `apps.chatbot`.
   - Django ORM models with automatic slugs, reading time calculations, and SQLite relational constraints.
   - Django ModelForms and custom validation.
   - Standard Django Template Language (DTL) with template inheritance (`base.html`), includes, and custom tags.

2. **User Authentication & Profiles**:
   - Built-in Django authentication (`authenticate()`, `login()`, `logout()`).
   - Registration with full name parsing and unique username generation.
   - Login supporting either email or username with "Remember me" session persistence.
   - Author profile with biographical details, professional role, and avatar.

3. **Complete Editorial Blog Management (CRUD)**:
   - **Homepage**: Hero banner, featured story card, and latest stories 3-column grid.
   - **Explore Stories**: Category filtering (Travel, Technology, Lifestyle, Food, Education, Health) and live keyword search.
   - **Blog Details**: Rich article reading view, reading time estimate, cover image, and related stories.
   - **Create Blog**: Form with rich editorial toolbar (H1, H2, H3, bold, italic, quotes, lists, code), cover image upload with preview, and "Generate with AI" integration.
   - **Edit Blog**: Owner-only authorization checks (`PermissionDenied`).
   - **Delete Blog**: POST-only deletion with confirmation modal.
   - **My Blogs Dashboard**: Filter tabs for All, Published, and Draft stories with dynamic counts, plus table and card view options.

4. **Author Follow System**:
   - Authenticated readers can follow/unfollow authors.
   - Model-level `CheckConstraint` and view-level guards strictly prevent self-following.
   - Database `UniqueConstraint` prevents duplicate follow records.
   - Dynamic follow button with real-time status.

5. **Google Gemini AI Writing Assistant**:
   - Powered by the official `google-genai` Python SDK.
   - AI service layer isolated inside `apps/chatbot/services.py`.
   - Generates blog titles, short summaries (excerpts), and complete structured articles.
   - Floating AI Assistant widget on all pages + "Generate with AI" modal directly in the blog editor.
   - One-click insertion into `#id_title`, `#id_description`, and `#id_content`.
   - Built-in graceful fallback when offline or before setting an API key.

6. **Static Informational Pages**:
   - About page with platform purpose and vision.
   - Contact page with form validation and feedback notifications.
   - Privacy Policy page detailing data ethics and creative rights.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, Django 5.x / 6.x |
| **Architecture** | Django MVT (Model-View-Template) |
| **Database** | SQLite 3 via Django ORM |
| **Authentication** | Django built-in auth (`auth_user`) |
| **AI Integration** | Google Gemini API via official `google-genai` SDK |
| **Frontend Markup**| HTML5, Django Template Language (DTL) |
| **CSS & Design** | Bootstrap 5.3.3, Bootstrap Icons, Custom CSS |
| **Typography** | Lora (Editorial Serif Headlines), Plus Jakarta Sans (Body) |
| **JavaScript** | Vanilla JavaScript (ES6+), Fetch API, CSRF protection |
| **File Handling** | Pillow (Image uploads, cover photos, avatars) |

---

## 📁 Project Structure

```text
INKSPACE/
│
├── config/                         # Core Django configuration
│   ├── __init__.py
│   ├── settings.py                 # Project settings & Gemini config
│   ├── urls.py                     # Root URL routing & custom error handlers
│   ├── asgi.py                     # ASGI server entrypoint
│   └── wsgi.py                     # WSGI server entrypoint
│
├── apps/                           # Modular Django applications
│   ├── __init__.py
│   │
│   ├── accounts/                   # Authentication, profiles & follow system
│   │   ├── migrations/
│   │   ├── templates/accounts/     # login.html, signup.html, profile.html
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── forms.py                # SignUpForm, LoginForm, ProfileForm
│   │   ├── models.py               # Profile, Follow models
│   │   ├── urls.py                 # /accounts/login/, /accounts/signup/, etc.
│   │   ├── views.py                # signup_view, login_view, toggle_follow_view
│   │   └── tests.py
│   │
│   ├── blogs/                      # Blog CRUD, explore, & static views
│   │   ├── migrations/
│   │   ├── templates/blogs/        # blog_list, blog_detail, create_blog, etc.
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── forms.py                # BlogForm, ContactForm
│   │   ├── models.py               # Blog model with automatic slug generation
│   │   ├── urls.py                 # /, /explore/, /create/, /<slug>/, etc.
│   │   ├── views.py                # blog_list, blog_detail, my_blogs, etc.
│   │   └── tests.py
│   │
│   └── chatbot/                    # Google Gemini AI assistant
│       ├── migrations/
│       ├── templates/chatbot/      # chatbot_widget.html
│       ├── static/chatbot/css/     # chatbot.css
│       ├── static/chatbot/js/      # chatbot.js
│       ├── admin.py
│       ├── apps.py
│       ├── models.py               # AIGenerationLog audit model
│       ├── urls.py                 # /chatbot/generate-blog/, /chatbot/chat/
│       ├── views.py                # JSON endpoints with CSRF protection
│       ├── services.py             # GeminiService (google-genai SDK wrapper)
│       └── tests.py
│
├── templates/                      # Global template folder
│   ├── base.html                   # Master template skeleton
│   ├── includes/
│   │   ├── navbar.html             # Responsive navbar with user dropdown
│   │   ├── footer.html             # Footer with links and social profiles
│   │   └── messages.html           # Bootstrap alert notifications
│   └── errors/
│       ├── 403.html                # Custom Permission Denied view
│       ├── 404.html                # Custom Not Found view
│       └── 500.html                # Custom Server Error view
│
├── static/                         # Global static assets
│   ├── css/style.css               # Editorial green & off-white styles
│   ├── js/main.js                  # Global UI interactions
│   └── images/
│
├── media/                          # Uploaded user files
│   ├── blog_covers/                # Blog cover images
│   └── avatars/                    # User profile avatars
│
├── db.sqlite3                      # Relational SQLite database
├── manage.py                       # Django CLI entrypoint
├── requirements.txt                # Python dependencies
├── seed_db.py                      # Database seeder with sample stories & accounts
├── .env                            # Environment variables (private)
├── .env.example                    # Template environment variables
├── .gitignore
├── PROJECT_OVERVIEW.md             # In-depth architectural specification
├── LEARNING_GUIDE.md               # Complete Django learning walkthrough
└── README.md                       # Quick start and overview
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher
- `pip` package manager

### 2. Clone and Setup Environment
```bash
# Clone the repository
git clone <repo-url>
cd INKSPACE

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS / Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and configure your settings:
```env
SECRET_KEY=django-insecure-inkspace-dev-secret-key-166534-22c55e-2026
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Optional: Add your Google Gemini API key from https://aistudio.google.com/
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
> **Note**: Even without a `GEMINI_API_KEY`, the application runs completely! The AI Writing Assistant includes a realistic editorial generator fallback so you can test content generation right away.

### 4. Run Migrations & Seed Database
```bash
# Run database migrations
python manage.py migrate

# Seed database with sample articles, authors, and relationships
python seed_db.py
```

### 5. Start the Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser!

---

## 👤 Demo User Accounts

The database comes pre-seeded with sample authors. You can log in using any of the following accounts:

| Username | Email | Password | Role |
|---|---|---|---|
| `akhilesh` | `akhilesh@example.com` | `Password123!` | Blogger · Developer (Admin) |
| `sneha` | `sneha@example.com` | `Password123!` | Travel Photojournalist |
| `akhil` | `akhil@example.com` | `Password123!` | Software Engineer |
| `fathima` | `fathima@example.com` | `Password123!` | Lifestyle Writer |

---

## 🧪 Running Automated Unit Tests

Run Django's built-in test runner across all apps:
```bash
python manage.py test
```

Tests cover:
- User signup and authentication (`apps/accounts/tests.py`)
- Unique email and password confirmation validation
- Follow and unfollow operations and self-follow prevention
- Blog creation, slug uniqueness, and draft publishing (`apps/blogs/tests.py`)
- Owner-only authorization on edit/delete actions
- Chatbot JSON API endpoints and input validation (`apps/chatbot/tests.py`)

---

## 📚 Educational Documentation

For a thorough understanding of Django internals:
- **[`PROJECT_OVERVIEW.md`](./PROJECT_OVERVIEW.md)**: Features mapping from TypeScript to Django, detailed architecture diagrams, database schema specifications, and security policies.
- **[`LEARNING_GUIDE.md`](./LEARNING_GUIDE.md)**: Step-by-step code explanations for every file, view, model, form, and the Gemini API service layer.
