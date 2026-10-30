from django.contrib import admin
from .models import Venue


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'status', 'address')
    list_filter = ('status',)
    search_fields = ('name', 'address')
