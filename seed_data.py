"""
Seed script - populates the database with realistic test data.
Run with: python manage.py shell < seed_data.py
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_system.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from events.models import Event, Registration, OrganizerProfile

print("Seeding Event Registration System...")

# Create superuser
admin, _ = User.objects.get_or_create(username='admin', defaults={
    'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True,
    'first_name': 'Admin', 'last_name': 'User'
})
admin.set_password('admin123')
admin.save()

# Organizers
organizers_data = [
    ('organizer1', 'org1@techconf.com', 'TechConf', 'Sarah', 'Johnson'),
    ('organizer2', 'org2@devmeetup.com', 'DevMeetup', 'James', 'Williams'),
]
organizers = []
for username, email, org, first, last in organizers_data:
    u, _ = User.objects.get_or_create(username=username, defaults={
        'email': email, 'first_name': first, 'last_name': last
    })
    u.set_password('password123')
    u.save()
    OrganizerProfile.objects.get_or_create(user=u, defaults={'organization': org, 'is_verified': True})
    organizers.append(u)

# Regular users
users = []
for i in range(1, 6):
    u, _ = User.objects.get_or_create(username=f'user{i}', defaults={
        'email': f'user{i}@mail.com', 'first_name': f'User', 'last_name': f'{i}'
    })
    u.set_password('password123')
    u.save()
    users.append(u)

now = timezone.now()

events_data = [
    {
        'title': 'PyCon Central Asia 2026',
        'description': 'Annual Python conference featuring talks on web dev, data science, and AI. Join 500+ developers!',
        'category': 'conference',
        'location': 'Baku Congress Center, Baku, Azerbaijan',
        'date': now + timedelta(days=10),
        'end_date': now + timedelta(days=12),
        'capacity': 200, 'price': 49.99, 'organizer': organizers[0],
    },
    {
        'title': 'Django REST Framework Deep Dive Workshop',
        'description': 'Hands-on 4-hour workshop covering DRF serializers, viewsets, authentication, and deployment.',
        'category': 'workshop',
        'location': 'Startup Yard, Baku, Azerbaijan',
        'date': now + timedelta(days=5),
        'capacity': 30, 'price': 25.00, 'organizer': organizers[0],
    },
    {
        'title': 'DevMeetup #42 - Microservices & Docker',
        'description': 'Monthly developer meetup. This time: Docker, Kubernetes, and microservices architecture in practice.',
        'category': 'meetup',
        'location': 'Garage Hub, Baku',
        'date': now + timedelta(days=3),
        'capacity': 80, 'price': 0.00, 'organizer': organizers[1],
    },
    {
        'title': 'AI & Machine Learning Webinar 2026',
        'description': 'Online deep-dive into GPT-4, RAG pipelines, and LLM fine-tuning for production apps.',
        'category': 'webinar',
        'location': 'Online (Zoom)',
        'date': now + timedelta(days=15),
        'capacity': 500, 'price': 0.00, 'organizer': organizers[1],
    },
    {
        'title': 'React & TypeScript Bootcamp',
        'description': 'Two-day intensive workshop building a full-stack app with React 19, TypeScript and Vite.',
        'category': 'workshop',
        'location': 'Code Academy, Baku',
        'date': now + timedelta(days=20),
        'end_date': now + timedelta(days=21),
        'capacity': 25, 'price': 35.00, 'organizer': organizers[0],
    },
]

events = []
for ed in events_data:
    e, _ = Event.objects.get_or_create(title=ed['title'], defaults=ed)
    events.append(e)

# Register users for events
reg_map = [
    (users[0], events[0]), (users[1], events[0]), (users[2], events[0]),
    (users[0], events[1]), (users[3], events[1]),
    (users[1], events[2]), (users[2], events[2]), (users[4], events[2]),
    (users[0], events[3]), (users[1], events[3]), (users[3], events[3]),
]
for u, e in reg_map:
    Registration.objects.get_or_create(user=u, event=e, defaults={'status': 'confirmed'})

print("✅ Done! Created:")
print(f"   {User.objects.count()} users  |  {Event.objects.count()} events  |  {Registration.objects.count()} registrations")
print("\nAdmin login:  admin / admin123")
print("Test user:    user1 / password123")
print("Organizer:    organizer1 / password123")
