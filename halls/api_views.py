from django.db.models import Prefetch

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import DjangoModelPermissions

from reservations.models import Reservation

from .models import Hall, HallStatus
from .serializers import HallSerializer


class HallModelPermissions(DjangoModelPermissions):
    perms_map = {
        **DjangoModelPermissions.perms_map,
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
    }


class HallVisibilityMixin:
    def get_queryset(self):
        queryset = Hall.objects.select_related('venue').prefetch_related(
            Prefetch(
                'reservations',
                queryset=Reservation.objects.only('sala_id', 'fecha_evento', 'estado'),
            )
        )
        if not self.request.user.has_perm('halls.change_hall'):
            queryset = queryset.filter(status=HallStatus.DISPONIBLE)
        return queryset


class HallListAPIView(HallVisibilityMixin, ListAPIView):
    serializer_class = HallSerializer
    permission_classes = [HallModelPermissions]

    def get_queryset(self):
        return super().get_queryset().order_by('name')


class HallDetailAPIView(HallVisibilityMixin, RetrieveAPIView):
    serializer_class = HallSerializer
    permission_classes = [HallModelPermissions]
