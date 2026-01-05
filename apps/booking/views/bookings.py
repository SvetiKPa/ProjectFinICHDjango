from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.booking.permissions import (IsOwner,
                                      IsOwnerOrReadOnly,
                                      CanCancelBooking,
                                      IsLessor)
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.booking.models import Booking
from apps.booking.serializers import (BookingSerializer,
                                      BookingCreateSerializer,
                                      BookingUpdateSerializer,
                                      CancelBookingSerializer,
                                      ConfirmBookingSerializer,
                                      BookingListSerializer)
from rest_framework.viewsets import ModelViewSet
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, BaseFilterBackend, OrderingFilter
from apps.booking.enums import BookingStatus
from django.db.models import Q

# class BookingViewSet(ModelViewSet):
#     queryset = Booking.objects.all()
#     serializer_class = BookingSerializer
#     permission_classes = [IsAuthenticated]


class BookingViewSet(ModelViewSet):
    """ViewSet для управления бронированиями"""

    queryset = Booking.objects.filter(is_deleted=False)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'listing', 'lessee', 'is_paid']
    ordering_fields = ['check_in_date', 'created_at', 'total_amount']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return BookingUpdateSerializer
        elif self.action == 'list':
            return BookingListSerializer
        return BookingSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwner()]
        elif self.action == 'cancel':
            return[IsAuthenticated(), CanCancelBooking()]
        elif self.action =='confirm':
            return [IsAuthenticated(), IsLessor()]
        elif self.action in ['list', 'retrieve', 'active', 'completed', 'cancelled']:
            return [IsAuthenticated()]

        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            if hasattr(user, 'role') and user.role == 'lessor':
                return Booking.objects.filter(
                    Q(listing__lessor=user) | Q(lessee=user)
                )
            else:
                return Booking.objects.filter(lessee=user)

        return Booking.objects.none()

    @action(detail=True, methods=['post'], permission_classes=[CanCancelBooking])
    def cancel(self, request, pk=None):
        """Отмена бронирования"""
        booking = self.get_object()
        serializer = CancelBookingSerializer(
            data=request.data,
            context={'booking': booking}
        )

        if serializer.is_valid():
            booking.mark_as_cancelled(
                user=request.user,
                reason=serializer.validated_data.get('reason', '')
            )
            return Response(
                {'status': 'Бронирование отменено'},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrReadOnly])
    def confirm(self, request, pk=None):
        """Подтверждение бронирования владельцем"""
        booking = self.get_object()
        if booking.listing.lessor != request.user:
            return Response(
                {'error': 'Только владелец жилья может подтверждать бронирования'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ConfirmBookingSerializer(data=request.data)
        if serializer.is_valid():
            action = serializer.validated_data['action']

            if action == 'confirm':
                booking.mark_as_confirmed(confirmed_by=request.user)
                return Response(
                    {'status': 'Бронирование подтверждено'},
                    status=status.HTTP_200_OK
                )
            else:
                booking.mark_as_cancelled(
                    user=request.user,
                    reason=serializer.validated_data.get('reason', 'Отклонено владельцем')
                )
                return Response(
                    {'status': 'Бронирование отклонено'},
                    status=status.HTTP_200_OK
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get'])
    def completed(self, request):
        """завершенные бронирования"""
        queryset = self.get_queryset().filter(
            status=BookingStatus.COMPLETED.value,
            check_out_date__lt=timezone.now().date()
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """активные бронирования"""
        queryset = self.get_queryset().filter(
            status__in=[
                BookingStatus.CONFIRMED.value,
                BookingStatus.ACTIVE.value
            ],
            check_out_date__gte=timezone.now().date()
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


    @action(detail=False, methods=['get'])
    def cancelled(self, request):
        """   Отмененные бронирования
        GET /api/v1/bookings/cancelled/
        """
        queryset = self.get_queryset().filter(
            status=BookingStatus.CANCELLED.value
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
