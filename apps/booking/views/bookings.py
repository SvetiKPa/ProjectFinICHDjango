from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.booking.permissions import IsOwner, IsOwnerOrReadOnly, CanCancelBooking
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
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return BookingUpdateSerializer
        elif self.action == 'list':
            return BookingListSerializer
        return BookingSerializer

    # permission_classes = []
    def get_permissions(self):
        """Настройка прав доступа"""
        # Для всех действий требуется аутентификация
        permission_classes = [IsAuthenticated]
        # Дополнительные проверки для конкретных действий
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes.append(IsOwner)
        elif self.action == 'cancel':
            permission_classes.append(CanCancelBooking)
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Фильтрация queryset в зависимости от пользователя"""
        user = self.request.user

        if not user.is_authenticated:
            return Booking.objects.none()

        queryset = super().get_queryset()

        # Админы видят все бронирования
        if user.is_staff:
            return queryset

        # Обычные пользователи видят только свои бронирования
        # и бронирования своих объявлений
        return queryset.filter(
            Q(lessee=user) | Q(listing__lessor=user)
        )

    def perform_create(self, serializer):
        """Создание нового бронирования"""
        booking = serializer.save(
            lessee=self.request.user,
            status=BookingStatus.PENDING.value
        )

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

        # Проверяем, что пользователь - владелец жилья
        if booking.listing.host != request.user:
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
    def my_bookings(self, request):
        """Получение бронирований текущего пользователя"""
        queryset = self.get_queryset().filter(lessee=request.user)

        # Фильтрация по статусу если указана
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Фильтрация активных/завершенных
        show_active = request.query_params.get('active')
        if show_active == 'true':
            queryset = queryset.filter(
                status__in=[
                    BookingStatus.PENDING.value,
                    BookingStatus.CONFIRMED.value,
                    BookingStatus.ACTIVE.value
                ]
            )
        elif show_active == 'false':
            queryset = queryset.filter(
                status__in=[
                    BookingStatus.CANCELLED.value,
                    BookingStatus.COMPLETED.value
                ]
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_listing_bookings(self, request):
        """Получение бронирований для жилья владельца"""
        queryset = self.get_queryset()

        # Дополнительная фильтрация
        listing_id = request.query_params.get('listing_id')
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)

        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Предстоящие бронирования"""
        queryset = self.get_queryset().filter(
            lessee=request.user,
            check_in_date__gte=timezone.now().date(),
            status__in=[BookingStatus.CONFIRMED.value, BookingStatus.ACTIVE.value]
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def past(self, request):
        """Прошедшие бронирования"""
        queryset = self.get_queryset().filter(
            lessee=request.user,
            check_out_date__lt=timezone.now().date()
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


