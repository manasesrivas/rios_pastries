from rest_framework import serializers

from reservations.models import INACTIVE_RESERVATION_STATES
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
    reservedDates = serializers.SerializerMethodField()

    def get_reservedDates(self, obj):
        return sorted(
            reservation.fecha_evento.isoformat()
            for reservation in obj.reservations.all()
            if reservation.estado not in INACTIVE_RESERVATION_STATES
        )

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
            'reservedDates',
        )
