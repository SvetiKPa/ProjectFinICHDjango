from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from apps.booking.models import Calendar, Listing, Booking
from apps.booking.serializers import CalendarAvailabilityCheckSerializer
from apps.booking.enums import AvailabilityStatus, BookingStatus


class CalendarViewSet(viewsets.ModelViewSet):
    """
    Минимальный ModelViewSet для календаря доступности
    """
    queryset = Calendar.objects.filter(is_deleted=False)
    serializer_class = CalendarAvailabilityCheckSerializer

    def get_queryset(self):
        """Базовая фильтрация"""
        queryset = super().get_queryset()

        # Фильтр по listing_id
        listing_id = self.request.query_params.get('listing_id')
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)

        return queryset.order_by('target_date', 'time_slot')

    @action(detail=False, methods=['post'])
    def check_availability(self, request):
        """
        Единственная необходимая функция - проверка доступности
        POST /api/v1/calendars/check_availability/
        """
        serializer = CalendarAvailabilityCheckSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        listing = serializer.validated_data['listing']
        check_in = serializer.validated_data['check_in_date']
        check_out = serializer.validated_data['check_out_date']

        # Проверяем доступность через календарь
        is_available = self._check_date_availability(listing, check_in, check_out)

        return Response({
            'is_available': is_available,
            'listing_id': listing.id,
            'check_in_date': check_in.isoformat(),
            'check_out_date': check_out.isoformat()
        })

    def _check_date_availability(self, listing, check_in, check_out):
        """
        Проверка доступности дат
        """
        # 1. Проверяем записи в календаре (если есть)
        booked_in_calendar = Calendar.objects.filter(
            listing=listing,
            target_date__gte=check_in,
            target_date__lt=check_out,
            availability=AvailabilityStatus.BOOKED
        ).exists()

        if booked_in_calendar:
            return False

        # 2. Проверяем бронирования
        booked_in_bookings = Booking.objects.filter(
            listing=listing,
            check_in_date__lt=check_out,
            check_out_date__gt=check_in,
            status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.ACTIVE],
            is_deleted=False
        ).exists()

        return not booked_in_bookings