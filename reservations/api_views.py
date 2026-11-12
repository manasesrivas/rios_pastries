from django.db.models import Prefetch

from rest_framework import status
from rest_framework.generics import CreateAPIView, ListCreateAPIView
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from products_reservations.models import ReservationItem

from .models import EstadoReservacion, Reservation
from .permissions import can_manage_reservations
from .serializers import ReservationCreateSerializer, ReservationSerializer


class ReservationModelPermissions(DjangoModelPermissions):
    perms_map = {
        **DjangoModelPermissions.perms_map,
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
    }


class ReservationCreateMixin:
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        reservation = serializer.save()
        reservation = Reservation.objects.select_related('sala__venue').prefetch_related(
            Prefetch('items', queryset=ReservationItem.objects.select_related('product')),
        ).get(pk=reservation.pk)
        response_serializer = ReservationSerializer(
            reservation, context=self.get_serializer_context(),
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ReservationListAPIView(ReservationCreateMixin, ListCreateAPIView):
    queryset = Reservation.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, ReservationModelPermissions]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReservationCreateSerializer
        return ReservationSerializer

    def get_queryset(self):
        queryset = Reservation.objects.select_related(
            'cliente',
            'sala',
            'sala__venue',
        ).prefetch_related(
            Prefetch('items', queryset=ReservationItem.objects.select_related('product')),
        ).exclude(
            estado=EstadoReservacion.ELIMINADA,
        ).order_by('-fecha_evento', '-pk')

        if not can_manage_reservations(self.request.user):
            queryset = queryset.filter(cliente=self.request.user)

        return queryset


class ReservationCreateAPIView(ReservationCreateMixin, CreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationCreateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, ReservationModelPermissions]
