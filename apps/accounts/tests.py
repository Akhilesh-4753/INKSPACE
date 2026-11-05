from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

class AccountTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='akhilesh',
            email='akhilesh@example.com',
            password='Password123!',
            first_name='Akhilesh',
            last_name='P'
        )

    def test_signup_page_status_code(self):
        response = self.client.get(reverse('accounts:signup'))
        self.assertEqual(response.status_code, 200)

    def test_login_page_status_code(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_successful_with_email(self):
        response = self.client.post(reverse('accounts:login'), {
            'username_or_email': 'akhilesh@example.com',
            'password': 'Password123!',
        })
        self.assertEqual(response.status_code, 302)

    def test_logout(self):
        self.client.login(username='akhilesh', password='Password123!')
        response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
