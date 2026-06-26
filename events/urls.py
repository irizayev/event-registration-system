from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/profile/', views.ProfileView.as_view(), name='profile'),

    # Events
    path('events/', views.EventListView.as_view(), name='event-list'),
    path('events/create/', views.EventCreateView.as_view(), name='event-create'),
    path('events/my/', views.OrganizerEventsView.as_view(), name='my-events'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event-detail'),
    path('events/<int:pk>/edit/', views.EventUpdateView.as_view(), name='event-edit'),
    path('events/<int:event_id>/stats/', views.event_stats, name='event-stats'),
    path('events/<int:event_id>/attendees/', views.EventAttendeesView.as_view(), name='event-attendees'),

    # Registrations
    path('events/<int:event_id>/register/', views.RegisterForEventView.as_view(), name='event-register'),
    path('events/<int:event_id>/cancel/', views.CancelRegistrationView.as_view(), name='event-cancel'),
    path('registrations/my/', views.MyRegistrationsView.as_view(), name='my-registrations'),
]
