from django.contrib import admin
from .models import Event, Registration, OrganizerProfile


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'date', 'location', 'capacity', 'available_spots', 'organizer', 'is_active']
    list_filter = ['category', 'is_active', 'date']
    search_fields = ['title', 'description', 'location']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']

    def available_spots(self, obj):
        return obj.available_spots
    available_spots.short_description = 'Available Spots'


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'status', 'ticket_code', 'registered_at']
    list_filter = ['status', 'registered_at']
    search_fields = ['user__username', 'event__title', 'ticket_code']
    readonly_fields = ['ticket_code', 'registered_at']


@admin.register(OrganizerProfile)
class OrganizerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'is_verified']
    list_filter = ['is_verified']
