from rest_framework import serializers

from .models import Hall


class HallSerializer(serializers.ModelSerializer):
    venueName = serializers.CharField(source='venue.name', read_only=True)

    class Meta:
        model = Hall
        fields = (
            'id',
            'venueName',
            'name',
            'image',
            'capacity',
            'price',
            'status',
        )
