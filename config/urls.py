"""
INKSPACE Project URL Configuration.

Routes:
- admin/ -> Django admin site
- accounts/ -> User authentication (login, signup, logout, profile)
- blogs/ & / -> Blog views (homepage, details, create, edit, my-blogs)
- chatbot/ -> AI Writing Assistant endpoints
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('', include('apps.blogs.urls', namespace='blogs')),
    path('chatbot/', include('apps.chatbot.urls', namespace='chatbot')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler403 = 'apps.blogs.views.custom_403_view'
handler404 = 'apps.blogs.views.custom_404_view'
handler500 = 'apps.blogs.views.custom_500_view'
