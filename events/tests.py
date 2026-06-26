from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from datetime import timedelta
from .models import Event, Registration


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_user(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'strongpass123',
            'password2': 'strongpass123',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)

    def test_register_password_mismatch(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'pass1234',
            'password2': 'different',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        User.objects.create_user(username='testuser', password='pass1234')
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'pass1234',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'nobody',
            'password': 'wrong',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EventTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organizer = User.objects.create_user(username='organizer', password='pass1234')
        self.user = User.objects.create_user(username='user1', password='pass1234')
        self.token_org = Token.objects.create(user=self.organizer)
        self.token_user = Token.objects.create(user=self.user)
        self.event = Event.objects.create(
            title='Test Conference',
            description='A test event',
            category='conference',
            location='Baku',
            date=timezone.now() + timedelta(days=10),
            capacity=50,
            price=10.00,
            organizer=self.organizer,
        )

    def test_list_events_public(self):
        response = self.client.get('/api/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_event_detail_public(self):
        response = self.client.get(f'/api/events/{self.event.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Conference')

    def test_create_event_requires_auth(self):
        response = self.client.post('/api/events/create/', {
            'title': 'New Event',
            'description': 'desc',
            'category': 'meetup',
            'location': 'Online',
            'date': (timezone.now() + timedelta(days=5)).isoformat(),
            'capacity': 30,
            'price': 0,
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_event_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_org.key}')
        response = self.client.post('/api/events/create/', {
            'title': 'New Event',
            'description': 'A great event',
            'category': 'meetup',
            'location': 'Online',
            'date': (timezone.now() + timedelta(days=5)).isoformat(),
            'capacity': 30,
            'price': 0,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_event_available_spots(self):
        self.assertEqual(self.event.available_spots, 50)
        Registration.objects.create(user=self.user, event=self.event, status='confirmed')
        self.assertEqual(self.event.available_spots, 49)

    def test_event_is_upcoming(self):
        self.assertTrue(self.event.is_upcoming)

    def test_search_events(self):
        response = self.client.get('/api/events/?search=Conference')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['count'], 0)


class RegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organizer = User.objects.create_user(username='organizer', password='pass1234')
        self.user = User.objects.create_user(username='user1', password='pass1234')
        self.token = Token.objects.create(user=self.user)
        self.event = Event.objects.create(
            title='Workshop',
            description='Hands-on workshop',
            category='workshop',
            location='Baku',
            date=timezone.now() + timedelta(days=5),
            capacity=2,
            price=0,
            organizer=self.organizer,
        )

    def test_register_for_event(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(f'/api/events/{self.event.id}/register/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('ticket_code', response.data)

    def test_cannot_register_twice(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.client.post(f'/api/events/{self.event.id}/register/')
        response = self.client.post(f'/api/events/{self.event.id}/register/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_register_when_full(self):
        # Fill up capacity
        for i in range(2):
            u = User.objects.create_user(username=f'filler{i}', password='pass')
            Registration.objects.create(user=u, event=self.event, status='confirmed')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(f'/api/events/{self.event.id}/register/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_registration(self):
        Registration.objects.create(user=self.user, event=self.event, status='confirmed')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(f'/api/events/{self.event.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_my_registrations(self):
        Registration.objects.create(user=self.user, event=self.event, status='confirmed')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get('/api/registrations/my/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_ticket_code_auto_generated(self):
        reg = Registration.objects.create(user=self.user, event=self.event, status='confirmed')
        self.assertTrue(len(reg.ticket_code) == 10)
        self.assertTrue(reg.ticket_code.isupper() or reg.ticket_code.isalnum())
