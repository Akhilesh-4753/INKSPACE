"""
Downloads or generates real images for the INKSPACE demo database.
Saves them to media/blog_covers/ and media/avatars/ so Django can serve them locally!
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

import requests
from PIL import Image, ImageDraw, ImageFont
from apps.blogs.models import Blog
from apps.accounts.models import Profile

MEDIA_DIR = BASE_DIR / 'media'
BLOG_COVERS_DIR = MEDIA_DIR / 'blog_covers'
AVATARS_DIR = MEDIA_DIR / 'avatars'

BLOG_COVERS_DIR.mkdir(parents=True, exist_ok=True)
AVATARS_DIR.mkdir(parents=True, exist_ok=True)

# Image mapping: (slug/filename, unsplash_url, fallback_color, title)
BLOG_IMAGES = {
    'a-weekend-in-the-western-ghats': (
        'western_ghats.jpg',
        'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
        (22, 101, 52), # #166534
        'Western Ghats Mist'
    ),
    'exploring-keralas-backwaters': (
        'backwaters.jpg',
        'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=800&q=80',
        (13, 148, 136), # Teal
        'Kerala Backwaters'
    ),
    'why-i-switched-to-django-for-my-projects': (
        'django_switch.jpg',
        'https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=800&q=80',
        (30, 41, 59), # Slate
        'Django Development'
    ),
    'small-habits-that-made-me-more-productive': (
        'habits.jpg',
        'https://images.unsplash.com/photo-1499750310107-5fef28a66643?auto=format&fit=crop&w=800&q=80',
        (180, 83, 9), # Amber
        'Daily Habits'
    ),
    'my-productivity-setup-for-2026': (
        'setup.jpg',
        'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80',
        (67, 56, 202), # Indigo
        'Productivity Workspace'
    ),
    'a-day-in-munnar-itinerary-and-tips': (
        'munnar.jpg',
        'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=800&q=80',
        (34, 197, 94), # Emerald
        'Munnar Tea Gardens'
    ),
    'django-vs-flask-which-one-to-choose': (
        'django_flask.jpg',
        'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=800&q=80',
        (15, 23, 42), # Dark Navy
        'Python Web Frameworks'
    ),
}

AVATAR_IMAGES = {
    'akhilesh': (
        'akhilesh.jpg',
        'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80',
        (22, 101, 52),
        'AP'
    ),
    'sneha': (
        'sneha.jpg',
        'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=300&q=80',
        (190, 24, 93),
        'SR'
    ),
    'akhil': (
        'akhil.jpg',
        'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=300&q=80',
        (37, 99, 235),
        'AN'
    ),
    'fathima': (
        'fathima.jpg',
        'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&w=300&q=80',
        (124, 58, 237),
        'FS'
    ),
}

def create_fallback_image(path, size, color, text):
    img = Image.new('RGB', size, color=color)
    draw = ImageDraw.Draw(img)
    # Simple centered text
    w, h = size
    # Draw simple cross patterns or border for visual appeal
    draw.rectangle([10, 10, w - 10, h - 10], outline=(255, 255, 255), width=3)
    img.save(path, 'JPEG', quality=85)

print("Downloading or generating blog covers...")
for slug, (filename, url, color, title) in BLOG_IMAGES.items():
    file_path = BLOG_COVERS_DIR / filename
    if not file_path.exists():
        downloaded = False
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(resp.content)
                downloaded = True
                print(f"Downloaded cover: {filename}")
        except Exception as e:
            pass
        if not downloaded:
            create_fallback_image(file_path, (1200, 675), color, title)
            print(f"Generated fallback cover: {filename}")

    # Update database blog record
    try:
        blog = Blog.objects.filter(slug=slug).first()
        if blog:
            blog.cover_image = f"blog_covers/{filename}"
            blog.save(update_fields=['cover_image'])
            print(f"Updated blog '{slug}' cover_image -> blog_covers/{filename}")
    except Exception as e:
        print(f"Error updating blog {slug}: {e}")

print("\nDownloading or generating author avatars...")
for username, (filename, url, color, initials) in AVATAR_IMAGES.items():
    file_path = AVATARS_DIR / filename
    if not file_path.exists():
        downloaded = False
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(resp.content)
                downloaded = True
                print(f"Downloaded avatar: {filename}")
        except Exception as e:
            pass
        if not downloaded:
            create_fallback_image(file_path, (300, 300), color, initials)
            print(f"Generated fallback avatar: {filename}")

    # Update database profile record
    try:
        profile = Profile.objects.filter(user__username=username).first()
        if profile:
            profile.avatar = f"avatars/{filename}"
            profile.save(update_fields=['avatar'])
            print(f"Updated profile '{username}' avatar -> avatars/{filename}")
    except Exception as e:
        print(f"Error updating profile {username}: {e}")

print("\nAll dummy images have been successfully processed!")

