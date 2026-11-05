from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('generate-blog/', views.generate_blog_api, name='generate_blog_api'),
    path('chat/', views.chat_message_api, name='chat_message_api'),
    path('widget/', views.chatbot_widget_view, name='chatbot_widget'),
]
