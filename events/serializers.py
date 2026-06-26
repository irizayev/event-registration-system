from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Event, Registration, OrganizerProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, label='Confirm password')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class OrganizerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OrganizerProfile
        fields = ['id', 'user', 'organization', 'bio', 'website', 'is_verified']


class EventListSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(source='organizer.username', read_only=True)
    available_spots = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    registration_count = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'category', 'location', 'date', 'end_date',
            'capacity', 'price', 'organizer_name', 'image_url',
            'available_spots', 'is_full', 'is_upcoming', 'registration_count', 'is_active'
        ]

    def get_registration_count(self, obj):
        return obj.registrations.filter(status='confirmed').count()


class EventDetailSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    available_spots = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    registration_count = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = '__all__'

    def get_registration_count(self, obj):
        return obj.registrations.filter(status='confirmed').count()


class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        exclude = ['organizer', 'created_at', 'updated_at']

    def validate(self, attrs):
        from django.utils import timezone
        if attrs.get('date') and attrs['date'] < timezone.now():
            raise serializers.ValidationError({'date': 'Event date cannot be in the past.'})
        if attrs.get('end_date') and attrs.get('date') and attrs['end_date'] < attrs['date']:
            raise serializers.ValidationError({'end_date': 'End date must be after start date.'})
        return attrs


class RegistrationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_date = serializers.DateTimeField(source='event.date', read_only=True)
    event_location = serializers.CharField(source='event.location', read_only=True)

    class Meta:
        model = Registration
        fields = [
            'id', 'user', 'event', 'event_title', 'event_date',
            'event_location', 'status', 'registered_at', 'notes', 'ticket_code'
        ]
        read_only_fields = ['ticket_code', 'registered_at']

    def validate(self, attrs):
        event = attrs.get('event')
        request = self.context.get('request')
        if event and event.is_full:
            raise serializers.ValidationError({'event': 'This event is fully booked.'})
        if event and not event.is_upcoming:
            raise serializers.ValidationError({'event': 'Cannot register for a past event.'})
        if event and request:
            if Registration.objects.filter(user=request.user, event=event, status='confirmed').exists():
                raise serializers.ValidationError({'event': 'You are already registered for this event.'})
        return attrs
