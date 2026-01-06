from datetime import timedelta, datetime
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.booking.permissions import (IsOwner,
                                      IsOwnerOrReadOnly,
                                      CanCancelBooking,
                                      IsLessor)
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.booking.models import Booking, Listing
from apps.booking.serializers import (BookingSerializer,
                                      BookingCreateSerializer,
                                      BookingUpdateSerializer,
                                      CancelBookingSerializer,
                                      BookingListSerializer)
from rest_framework.viewsets import ModelViewSet
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from apps.booking.enums import BookingStatus
from apps.booking.availability import AvailabilityService
from django.db.models import Q


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
        elif self.action == 'check_availability':
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwner()]
        elif self.action == 'cancel':
            return[IsAuthenticated(), CanCancelBooking()]
        elif self.action in ['confirm', 'reject']:
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

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отмена бронирования"""
        booking = self.get_object()
        user = request.user

        is_lessee = booking.lessee == user
        is_lessor = booking.listing.lessor == user

        if not (is_lessee or is_lessor):
            return Response(
                {'error': 'Нет прав для отмены этого бронирования'},
                status=status.HTTP_403_FORBIDDEN
            )

        if is_lessee:
            if booking.status not in [BookingStatus.PENDING.value, BookingStatus.CONFIRMED.value]:
                return Response(
                    {'error': 'Можно отменить только ожидающие или подтвержденные бронирования'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Проверяем срок (за 2 дня до заезда)
            cancellation_deadline = booking.check_in_date - timedelta(days=2)
            if timezone.now().date() >= cancellation_deadline:
                return Response(
                    {'error': 'Отмена возможна только за 2 дня до заезда'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = CancelBookingSerializer(
            data=request.data,
            context={'booking': booking}
        )

        if serializer.is_valid():
            if booking.status in [
                BookingStatus.PENDING.value,
                BookingStatus.CONFIRMED.value
            ]:
                AvailabilityService.free_dates(
                    listing=booking.listing,
                    check_in_date=booking.check_in_date,
                    check_out_date=booking.check_out_date
                )

            booking.mark_as_cancelled(
                user=request.user,
                reason=serializer.validated_data.get('reason', '')
            )

            return Response(
                {
                    'success': True,
                    'message': 'Бронирование отменено',
                    'booking_id': booking.id,
                    'new_status': 'cancelled',
                    'cancelled_by': 'lessee' if is_lessee else 'lessor'
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Подтверждение бронирования владельцем"""
        booking = self.get_object()

        if booking.listing.lessor != request.user:
            return Response(
                {'error': 'Только владелец жилья может подтверждать бронирования'},
                status=status.HTTP_403_FORBIDDEN
            )

        if booking.status == BookingStatus.PENDING.value:
            # Блокируем даты в календаре
            AvailabilityService.block_dates(
                listing=booking.listing,
                check_in_date=booking.check_in_date,
                check_out_date=booking.check_out_date,
                booking=booking
            )

        booking.mark_as_confirmed(confirmed_by=request.user)

        return Response(
            {
                'success': True,
                'message': 'Бронирование подтверждено',
                'booking_id': booking.id,
                'new_status': 'confirmed',
                'confirmed_by': request.user.username,
                'confirmed_at': booking.confirmed_at
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Отклонение бронирования владельцем"""
        booking = self.get_object()

        if booking.listing.lessor != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Только владелец жилья может отклонять бронирования'},
                status=status.HTTP_403_FORBIDDEN
            )
        reason = request.data.get('reason', 'Отклонено владельцем')
        try:
            if reason and not isinstance(reason, str):
                reason = str(reason)
            if len(reason) > 500:
                reason = reason[:500]
        except:
            reason = 'Отклонено владельцем'

        if booking.status == BookingStatus.PENDING.value:
            AvailabilityService.free_dates(
                listing=booking.listing,
                check_in_date=booking.check_in_date,
                check_out_date=booking.check_out_date
            )

        booking.mark_as_cancelled(
            user=request.user,
            reason=reason
        )

        return Response(
            {
                'success': True,
                'message': 'Бронирование отклонено',
                'booking_id': booking.id,
                'new_status': 'rejected',
                'rejected_by': request.user.username,
                'reason': reason,
                'rejected_at': booking.cancelled_at
            },
            status=status.HTTP_200_OK
        )

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
        """   Отмененные бронирования        """
        queryset = self.get_queryset().filter(
            status=BookingStatus.CANCELLED.value
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='availability/check')
    def check_availability(self, request):
        """        Простая проверка доступности дат      """
        listing_id = request.GET.get('listing_id')
        check_in_str = request.GET.get('check_in_date')
        check_out_str = request.GET.get('check_out_date')

        if not all([listing_id, check_in_str, check_out_str]):
            return Response(
                {"error": "Необходимы: listing_id, check_in_date, check_out_date"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            listing = Listing.objects.get(id=listing_id)
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except:
            return Response({"error": "Некорректные данные"}, status=status.HTTP_400_BAD_REQUEST)

        is_available, message = AvailabilityService.check_availability(listing, check_in, check_out)

        return Response({
            "is_available": is_available,
            "message": message,
            "listing_id": listing_id,
            "check_in_date": check_in_str,
            "check_out_date": check_out_str
        })