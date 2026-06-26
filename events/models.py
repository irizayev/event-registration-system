from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string


CATS = [
    ('conference', 'Conference'),
    ('workshop', 'Workshop'),
    ('webinar', 'Webinar'),
    ('meetup', 'Meetup'),
    ('concert', 'Concert'),
    ('other', 'Other'),
]

REG_STATUS = [
    ('confirmed', 'Confirmed'),
    ('cancelled', 'Cancelled'),
    ('waitlisted', 'Waitlisted'),
]


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATS, default='other')
    location = models.CharField(max_length=300)
    date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    capacity = models.PositiveIntegerField(default=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    image_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return self.title

    @property
    def available_spots(self):
        taken = self.registrations.filter(status='confirmed').count()
        return self.capacity - taken

    @property
    def is_full(self):
        return self.available_spots <= 0

    @property
    def is_upcoming(self):
        return self.date > timezone.now()


class Registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    status = models.CharField(max_length=20, choices=REG_STATUS, default='confirmed')
    registered_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    ticket_code = models.CharField(max_length=20, unique=True, blank=True)

    class Meta:
        unique_together = ('user', 'event')
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.user.username} -> {self.event.title}"

    def save(self, *args, **kwargs):
        if not self.ticket_code:
            chars = string.ascii_uppercase + string.digits
            self.ticket_code = ''.join(random.choices(chars, k=10))
        super().save(*args, **kwargs)


class OrganizerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='organizer_profile')
    organization = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ({self.organization})"
