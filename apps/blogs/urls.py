from django.urls import path
from . import views

app_name = 'blogs'

urlpatterns = [
    path('', views.blog_list, name='blog_list'),
    path('explore/', views.explore_blogs, name='explore'),
    path('my-blogs/', views.my_blogs, name='my_blogs'),
    path('create/', views.create_blog, name='create_blog'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('<slug:slug>/edit/', views.edit_blog, name='edit_blog'),
    path('<slug:slug>/delete/', views.delete_blog, name='delete_blog'),
]
