from rest_framework.generics import ListAPIView
from rest_framework.permissions import DjangoModelPermissions

from .models import EstadoReservacion, Reservation
from .permissions import can_manage_reservations
from .serializers import ReservationSerializer


class ReservationModelPermissions(DjangoModelPermissions):
    perms_map = {
        **DjangoModelPermissions.perms_map,
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
    }


class ReservationListAPIView(ListAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [ReservationModelPermissions]

    def get_queryset(self):
        queryset = Reservation.objects.select_related(
            'cliente',
            'sala',
            'sala__venue',
        ).exclude(
            estado=EstadoReservacion.ELIMINADA,
        ).order_by('-fecha_evento', '-pk')

        if not can_manage_reservations(self.request.user):
            queryset = queryset.filter(cliente=self.request.user)

        return queryset
