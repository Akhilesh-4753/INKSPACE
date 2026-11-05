"""
Database seeder for INKSPACE SQLite database.
Generates db.sqlite3 with User and Blog schema and seed data matching the UI collage.
Uses proper Django PBKDF2 SHA256 password hashes so demo users can immediately log in with 'Password123!'.
"""
import sqlite3
import datetime
import hashlib
import base64

def make_django_pbkdf2_hash(password, salt='inkspacesalt2026', iterations=720000):
    """
    Computes a 100% Django-compatible PBKDF2 SHA256 password hash.
    Format: pbkdf2_sha256$<iterations>$<salt>$<base64_hash>
    """
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations,
        dklen=32
    )
    b64_hash = base64.b64encode(hash_bytes).decode('ascii').strip()
    return f'pbkdf2_sha256${iterations}${salt}${b64_hash}'

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

# Enable foreign keys
cur.execute('PRAGMA foreign_keys = ON;')

# Create auth_user table
cur.execute('''
CREATE TABLE IF NOT EXISTS auth_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME,
    is_superuser BOOLEAN NOT NULL,
    username VARCHAR(150) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    is_staff BOOLEAN NOT NULL,
    is_active BOOLEAN NOT NULL,
    date_joined DATETIME NOT NULL
);
''')

# Create accounts_profile table
cur.execute('''
CREATE TABLE IF NOT EXISTS accounts_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bio TEXT NOT NULL,
    role VARCHAR(100) NOT NULL,
    avatar VARCHAR(100),
    created_at DATETIME NOT NULL,
    user_id INTEGER NOT NULL UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE
);
''')

# Create accounts_follow table
cur.execute('''
CREATE TABLE IF NOT EXISTS accounts_follow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME NOT NULL,
    follower_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    following_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    CONSTRAINT unique_user_follow UNIQUE (follower_id, following_id),
    CONSTRAINT prevent_self_follow CHECK (follower_id != following_id)
);
''')

# Create blogs_blog table
cur.execute('''
CREATE TABLE IF NOT EXISTS blogs_blog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(300) NOT NULL UNIQUE,
    description VARCHAR(250) NOT NULL,
    cover_image VARCHAR(100),
    category VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,
    is_featured BOOLEAN NOT NULL,
    views_count INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    published_at DATETIME,
    author_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
);
''')

# Create chatbot_aigenerationlog table
cur.execute('''
CREATE TABLE IF NOT EXISTS chatbot_aigenerationlog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_summary VARCHAR(255) NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
);
''')

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
demo_pw_hash = make_django_pbkdf2_hash('Password123!')

# Seed Users (all can login with username and password 'Password123!')
users = [
    (1, demo_pw_hash, None, 1, 'akhilesh', 'Akhilesh', 'P', 'akhilesh@example.com', 1, 1, now),
    (2, demo_pw_hash, None, 0, 'sneha', 'Sneha', 'R', 'sneha@example.com', 0, 1, now),
    (3, demo_pw_hash, None, 0, 'akhil', 'Akhil', 'N', 'akhil@example.com', 0, 1, now),
    (4, demo_pw_hash, None, 0, 'fathima', 'Fathima', 'S', 'fathima@example.com', 0, 1, now),
]

for u in users:
    cur.execute('''
    INSERT OR REPLACE INTO auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', u)

# Seed Profiles
profiles = [
    (1, 'I write about travel, productivity, technology and everyday life experiences.', 'Blogger · Developer', 'avatars/akhilesh.jpg', now, 1),
    (2, 'Photographer and slow travel enthusiast documenting hidden trails.', 'Travel Photojournalist', 'avatars/sneha.jpg', now, 2),
    (3, 'Full stack engineer building elegant web tools with Python and Django.', 'Software Engineer', 'avatars/akhil.jpg', now, 3),
    (4, 'Exploring personal systems, reading habits, and mindful living.', 'Lifestyle Writer', 'avatars/fathima.jpg', now, 4),
]

for p in profiles:
    cur.execute('''
    INSERT OR REPLACE INTO accounts_profile (id, bio, role, avatar, created_at, user_id)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', p)

# Seed Follow Relationships (Akhilesh follows Sneha and Akhil; Sneha follows Akhilesh)
follows = [
    (1, now, 1, 2),  # Akhilesh -> Sneha
    (2, now, 1, 3),  # Akhilesh -> Akhil
    (3, now, 2, 1),  # Sneha -> Akhilesh
    (4, now, 4, 1),  # Fathima -> Akhilesh
]

for f in follows:
    cur.execute('''
    INSERT OR REPLACE INTO accounts_follow (id, created_at, follower_id, following_id)
    VALUES (?, ?, ?, ?)
    ''', f)

# Seed Blogs matching UI collage
blogs = [
    (
        1,
        'A Weekend in the Western Ghats: Nature, Peace and Perspective',
        'a-weekend-in-the-western-ghats',
        'A short escape to the misty hills of Kerala that reminded me how powerful and healing nature can be.',
        'blog_covers/western_ghats.jpg',
        'Travel',
        '''<p>The Western Ghats have always been a special place for me. This weekend, I took a short trip to one of its quiet hill stations in Kerala. The cool breeze, mist-covered hills, and the sound of nature all around made it a much-needed break from my routine.</p>
<h3>Escaping the City Rush</h3>
<p>Living in the city, it’s easy to get caught up in the constant rush of work and deadlines. Taking just two days to disconnect and immerse myself in greenery felt like hitting a refresh button. As the car wound up the mountain roads, the temperature dropped and the noise of traffic gave way to the soothing rustle of pine trees and distant waterfalls.</p>
<blockquote>"In every walk with nature, one receives far more than he seeks." – John Muir</blockquote>
<h3>Mornings in the Mist</h3>
<p>Waking up at 6:00 AM with cups of steaming black tea while looking out at rolling tea plantations draped in thick morning fog was unforgettable. Walking along damp trails with camera in hand, every turn revealed a new perspective—wild streams crashing over smooth stones, birds singing across the valley, and sunlight breaking through tree crowns.</p>
<h3>Key Takeaways</h3>
<ul>
  <li>Slow down intentionally: We do not need long vacations to recharge; 48 hours in quiet nature can restore focus.</li>
  <li>Carry minimal gear: Less time checking phone screens equals more time observing real life.</li>
  <li>Support local mountain communities and leave no trash behind.</li>
</ul>
<p>If you have been feeling drained or overwhelmed lately, consider planning a quiet weekend escape to the hills. You will return with a renewed sense of clarity and gratitude.</p>''',
        'Published',
        1,
        142,
        now,
        now,
        now,
        1
    ),
    (
        2,
        "Exploring Kerala's Backwaters: A Journey Through Serene Waters",
        'exploring-keralas-backwaters',
        'Gliding through emerald waterways, quiet village canals, and timeless houseboats in God’s Own Country.',
        'blog_covers/backwaters.jpg',
        'Travel',
        '<p>There is something timeless and serene about cruising the backwaters of Alappuzha. The gentle rhythm of water against wood, tall coconut palms leaning across the canals, and glimpses of traditional village life make this one of the most rejuvenating journeys on earth.</p>',
        'Published',
        0,
        98,
        now,
        now,
        now,
        2
    ),
    (
        3,
        'Why I Switched to Django for My Projects',
        'why-i-switched-to-django-for-my-projects',
        'Batteries included, clean MVT architecture, and seamless database operations changed how I build web tools.',
        'blog_covers/django_switch.jpg',
        'Technology',
        '<p>For years I bounced between micro-frameworks, stitching together authentication libraries, ORMs, and migration tooling. When I gave Django a serious evaluation for full-stack apps, the sheer cohesion of the MVT architecture won me over.</p>',
        'Published',
        0,
        215,
        now,
        now,
        now,
        3
    ),
    (
        4,
        'Small Habits That Made Me More Productive',
        'small-habits-that-made-me-more-productive',
        'Simple everyday adjustments that helped me write better, stay focused, and reduce mental fatigue.',
        'blog_covers/habits.jpg',
        'Lifestyle',
        '<p>Productivity is rarely about dramatic 180-degree life overhauls. It is almost always the compound result of small daily decisions: morning shutdown routines, single-tab writing sessions, and intentional pauses.</p>',
        'Published',
        0,
        180,
        now,
        now,
        now,
        4
    ),
    (
        5,
        'My Productivity Setup for 2026',
        'my-productivity-setup-for-2026',
        'The minimalist hardware and software tools keeping me in flow state while writing and coding.',
        'blog_covers/setup.jpg',
        'Lifestyle',
        '<p>A breakdown of my clean desk workspace, distraction-free text editors, and Gemini AI writing workflows.</p>',
        'Published',
        0,
        84,
        now,
        now,
        now,
        1
    ),
    (
        6,
        'A Day in Munnar: Itinerary & Tips',
        'a-day-in-munnar-itinerary-and-tips',
        'How to make the most of 24 hours among rolling tea gardens and fresh mountain air.',
        'blog_covers/munnar.jpg',
        'Travel',
        '<p>A detailed morning-to-night guide for travelers visiting Munnar with recommendations for scenic overlooks.</p>',
        'Published',
        0,
        110,
        now,
        now,
        now,
        1
    ),
    (
        7,
        'Django vs Flask: Which One to Choose in 2026?',
        'django-vs-flask-which-one-to-choose',
        'A comprehensive comparison of Python web frameworks for beginners and experienced developers.',
        'blog_covers/django_flask.jpg',
        'Technology',
        '<p>Draft in progress exploring ORM, authentication, and speed of delivery.</p>',
        'Draft',
        0,
        0,
        now,
        now,
        None,
        1
    ),
]

for b in blogs:
    cur.execute('''
    INSERT OR REPLACE INTO blogs_blog (id, title, slug, description, cover_image, category, content, status, is_featured, views_count, created_at, updated_at, published_at, author_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', b)

conn.commit()
conn.close()
print("Successfully generated db.sqlite3 with seed data and working authentication!")
