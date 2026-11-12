from rest_framework import serializers

from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    hallName = serializers.CharField(source='sala.name', read_only=True)
    venueName = serializers.CharField(source='sala.venue.name', read_only=True)
    venueAdress = serializers.CharField(
        source='sala.venue.address',
        read_only=True,
    )
    hall = serializers.SerializerMethodField()
    venue = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = (
            'id',
            'cliente',
            'fecha_evento',
            'cantidad_personas',
            'sala',
            'estado',
            'hallName',
            'venueName',
            'venueAdress',
            'hall',
            'venue',
        )

    def get_hall(self, obj):
        return None

    def get_venue(self, obj):
        return None
