from django.test import TestCase, Client
from django.urls import reverse
import json
from unittest.mock import patch
from apps.chatbot.services import GeminiService

class ChatbotEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.service = GeminiService()

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

    def test_dynamic_fallback_mentor_mode(self):
        # Test mentor response generation for a simple topic
        reply = self.service._generate_dynamic_fallback('Need food topic', 'general')
        self.assertIn('Suggested Blog Titles', reply)
        self.assertIn('Suggested Description', reply)
        self.assertIn('Content Ideas', reply)
        self.assertIn('Which idea would you like to develop into a complete blog?', reply)

    def test_dynamic_fallback_titles_mode(self):
        # Test catchy titles mode
        reply = self.service._generate_dynamic_fallback('Travel in Kerala', 'titles')
        self.assertIn('Kerala', reply)
        self.assertIn('1.', reply)

    def test_dynamic_fallback_description_mode(self):
        # Test short descriptions mode
        reply = self.service._generate_dynamic_fallback('Benefits of Python', 'description')
        self.assertIn('Option 1', reply)
        self.assertIn('Python', reply)

    def test_dynamic_fallback_ideas_mode(self):
        # Test content ideas and headings mode
        reply = self.service._generate_dynamic_fallback('Remote Work Productivity', 'ideas')
        self.assertIn('Target Audience', reply)
        self.assertIn('Recommended Content Outline', reply)

    def test_dynamic_fallback_improve_mode(self):
        # Test improve writing mode
        reply = self.service._generate_dynamic_fallback('Writing blogs helps people learn new things.', 'improve')
        self.assertIn('Polished Version', reply)
        self.assertIn('Key Improvements Made', reply)

    def test_dynamic_fallback_multiturn_flow(self):
        # Test conversation context remembering previous title choice
        history = [
            {'role': 'user', 'content': 'Travel in Kerala'},
            {'role': 'assistant', 'content': '1. Exploring Kerala\n2. The Secret Behind Kerala Food Culture\n3. Backwaters Guide'}
        ]
        reply = self.service._generate_dynamic_fallback('Generate the full blog for the second title', 'general', history)
        self.assertIn('Introduction', reply)
        self.assertIn('Conclusion', reply)

    @patch.object(GeminiService, 'chat_assist')
    def test_chat_view_endpoint(self, mock_assist):
        mock_assist.return_value = "Great! Here are 5 food blog ideas..."
        response = self.client.post(
            reverse('chatbot:chat_message_api'),
            data=json.dumps({
                'message': 'Need food topic',
                'mode': 'general',
                'history': []
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['reply'], "Great! Here are 5 food blog ideas...")
        self.assertEqual(data['mode'], 'general')
