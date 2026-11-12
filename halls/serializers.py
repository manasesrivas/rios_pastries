from rest_framework import serializers

from venues.models import Venue

from .models import Hall


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ('id', 'name', 'address', 'descripcion', 'status')
        read_only_fields = fields


class HallSerializer(serializers.ModelSerializer):
    venueName = serializers.CharField(source='venue.name', read_only=True)
    venue = VenueSerializer(read_only=True)

    class Meta:
        model = Hall
        fields = (
            'id',
            'venueName',
            'venue',
            'name',
            'image',
            'capacity',
            'price',
            'status',
        )
