from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.utils import timezone

from .models import Event, Registration
from .serializers import (
    EventListSerializer, EventDetailSerializer, EventCreateSerializer,
    RegistrationSerializer, RegisterUserSerializer, UserSerializer,
)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = RegisterUserSerializer(data=request.data)
        if s.is_valid():
            u = s.save()
            token, _ = Token.objects.get_or_create(user=u)
            return Response({
                'message': 'registered',
                'token': token.key,
                'user': UserSerializer(u).data
            }, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        u = authenticate(
            username=request.data.get('username'),
            password=request.data.get('password')
        )
        if u:
            token, _ = Token.objects.get_or_create(user=u)
            return Response({'token': token.key, 'user': UserSerializer(u).data})
        return Response({'error': 'wrong credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({'message': 'logged out'})


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class EventListView(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'location', 'category']
    ordering_fields = ['date', 'price', 'title']
    ordering = ['date']

    def get_queryset(self):
        qs = Event.objects.filter(is_active=True)
        cat = self.request.query_params.get('category')
        upcoming = self.request.query_params.get('upcoming')
        if cat:
            qs = qs.filter(category=cat)
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


class RegisterForEventView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, event_id):
        try:
            ev = Event.objects.get(pk=event_id, is_active=True)
        except Event.DoesNotExist:
            return Response({'error': 'not found'}, status=404)

        if ev.is_full:
            return Response({'error': 'event is full'}, status=400)
        if not ev.is_upcoming:
            return Response({'error': 'event already passed'}, status=400)

        reg, created = Registration.objects.get_or_create(
            user=request.user, event=ev,
            defaults={'notes': request.data.get('notes', ''), 'status': 'confirmed'}
        )
        if not created:
            if reg.status == 'cancelled':
                reg.status = 'confirmed'
                reg.save()
                return Response({'message': 'registration restored', 'ticket_code': reg.ticket_code})
            return Response({'error': 'already registered'}, status=400)

        return Response({
            'message': f'registered for {ev.title}',
            'ticket_code': reg.ticket_code,
            'registration_id': reg.id
        }, status=201)


class CancelRegistrationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, event_id):
        try:
            reg = Registration.objects.get(user=request.user, event_id=event_id)
        except Registration.DoesNotExist:
            return Response({'error': 'not found'}, status=404)
        reg.status = 'cancelled'
        reg.save()
        return Response({'message': 'cancelled'})


class MyRegistrationsView(generics.ListAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Registration.objects.filter(user=self.request.user)
        s = self.request.query_params.get('status')
        if s:
            qs = qs.filter(status=s)
        return qs


class EventAttendeesView(generics.ListAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        eid = self.kwargs['event_id']
        try:
            ev = Event.objects.get(pk=eid, organizer=self.request.user)
        except Event.DoesNotExist:
            return Registration.objects.none()
        return Registration.objects.filter(event=ev, status='confirmed')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def event_stats(request, event_id):
    try:
        ev = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return Response({'error': 'not found'}, status=404)
    return Response({
        'event_id': event_id,
        'title': ev.title,
        'capacity': ev.capacity,
        'confirmed': ev.registrations.filter(status='confirmed').count(),
        'cancelled': ev.registrations.filter(status='cancelled').count(),
        'available': ev.available_spots,
        'is_full': ev.is_full,
    })
