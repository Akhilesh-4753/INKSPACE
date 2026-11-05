from django.test import TestCase, Client
from django.urls import reverse
import json

class ChatbotEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_generate_blog_missing_topic(self):
        response = self.client.post(
            reverse('chatbot:generate_blog_api'),
            data=json.dumps({'topic': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_chat_message_empty(self):
        response = self.client.post(
            reverse('chatbot:chat_message_api'),
            data=json.dumps({'message': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
