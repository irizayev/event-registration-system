from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event, Registration, OrganizerProfile
from .serializers import (
    EventListSerializer, EventDetailSerializer, EventCreateSerializer,
    RegistrationSerializer, RegisterUserSerializer, UserSerializer,
    OrganizerProfileSerializer
)


# ─────────────────────────── AUTH ───────────────────────────

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'message': 'User registered successfully.',
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully.'})


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


# ─────────────────────────── EVENTS ───────────────────────────

class EventListView(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'location', 'category']
    ordering_fields = ['date', 'price', 'title']
    ordering = ['date']

    def get_queryset(self):
        qs = Event.objects.filter(is_active=True)
        category = self.request.query_params.get('category')
        upcoming = self.request.query_params.get('upcoming')
        from django.utils import timezone
        if category:
            qs = qs.filter(category=category)
        if upcoming == 'true':
            qs = qs.filter(date__gte=timezone.now())
        return qs


class EventDetailView(generics.RetrieveAPIView):
    queryset = Event.objects.all()
    serializer_class = EventDetailSerializer
    permission_classes = [permissions.AllowAny]


class EventCreateView(generics.CreateAPIView):
    serializer_class = EventCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)


class EventUpdateView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EventCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(organizer=self.request.user)


class OrganizerEventsView(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(organizer=self.request.user)


# ─────────────────────────── REGISTRATIONS ───────────────────────────

class RegisterForEventView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, event_id):
        try:
            event = Event.objects.get(pk=event_id, is_active=True)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)

        if event.is_full:
            return Response({'error': 'Event is fully booked.'}, status=status.HTTP_400_BAD_REQUEST)
        if not event.is_upcoming:
            return Response({'error': 'Cannot register for a past event.'}, status=status.HTTP_400_BAD_REQUEST)

        reg, created = Registration.objects.get_or_create(
            user=request.user, event=event,
            defaults={'notes': request.data.get('notes', ''), 'status': 'confirmed'}
        )
        if not created:
            if reg.status == 'cancelled':
                reg.status = 'confirmed'
                reg.save()
                return Response({'message': 'Registration restored.', 'ticket_code': reg.ticket_code})
            return Response({'error': 'Already registered.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': f'Successfully registered for {event.title}!',
            'ticket_code': reg.ticket_code,
            'registration_id': reg.id
        }, status=status.HTTP_201_CREATED)


class CancelRegistrationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, event_id):
        try:
            reg = Registration.objects.get(user=request.user, event_id=event_id)
        except Registration.DoesNotExist:
            return Response({'error': 'Registration not found.'}, status=status.HTTP_404_NOT_FOUND)

        reg.status = 'cancelled'
        reg.save()
        return Response({'message': 'Registration cancelled successfully.'})


class MyRegistrationsView(generics.ListAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        status_filter = self.request.query_params.get('status')
        qs = Registration.objects.filter(user=self.request.user)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class EventAttendeesView(generics.ListAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        event_id = self.kwargs['event_id']
        # Only organizer can view attendees
        try:
            event = Event.objects.get(pk=event_id, organizer=self.request.user)
        except Event.DoesNotExist:
            return Registration.objects.none()
        return Registration.objects.filter(event=event, status='confirmed')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def event_stats(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return Response({'error': 'Not found.'}, status=404)
    return Response({
        'event_id': event_id,
        'title': event.title,
        'capacity': event.capacity,
        'confirmed': event.registrations.filter(status='confirmed').count(),
        'cancelled': event.registrations.filter(status='cancelled').count(),
        'available_spots': event.available_spots,
        'is_full': event.is_full,
    })
