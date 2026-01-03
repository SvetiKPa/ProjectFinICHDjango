from rest_framework import serializers
from apps.booking.models import Booking
from apps.booking.enums import BookingStatus
from django.utils import timezone
from datetime import timedelta
# from apps.booking.serializers import CalendarSerializer

# Отсутствуют импорты для timezone, timedelta, CalendarService, BookingService в сериализаторах
# # CalendarService не импортирован:
# is_available = CalendarService.check_date_range_availability(...)
#
# # BookingService не импортирован:
# price_data = BookingService.calculate_booking_price(...)

class BookingSerializer(serializers.ModelSerializer):
    """Основной сериализатор для бронирований"""

    is_active = serializers.BooleanField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)
    nights_remaining = serializers.IntegerField(read_only=True)
    current_stay_progress = serializers.IntegerField(read_only=True)

    # Дополнительные поля
    lessee = serializers.ReadOnlyField(source='lessee.username')
    lessee_email = serializers.ReadOnlyField(source='lessee.email')
    lessee_phone = serializers.ReadOnlyField(source='lessee.phone')

    # Поля из связанного листинга :
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_address = serializers.SerializerMethodField(read_only=True)
    lessor_id = serializers.IntegerField(source='listing.lessor.id', read_only=True)
    lessor_name = serializers.CharField(source='listing.lessor.get_full_name', read_only=True)

    # Поля календаря
    # calendar_entries = CalendarSerializer(many=True, read_only=True, source='calendar_days')
    calendar_dates = serializers.SerializerMethodField(read_only=True)

    def get_calendar_dates(self, obj):
        """Получить даты из календаря"""
        if hasattr(obj, 'calendar_days'):
            return list(obj.calendar_days.values_list('target_date', flat=True))
        return []


    def get_listing_address(self, obj):
        if obj.listing and hasattr(obj.listing, 'address'):
            address = obj.listing.address
            if address:
                parts = []
                if hasattr(address, 'street') and address.street:
                    parts.append(address.street)
                if hasattr(address, 'city') and address.city:
                    parts.append(address.city)
                return ", ".join(parts)
        return "Адрес не указан"

    class Meta:
        model = Booking
        fields = [
            # Основная информация
            'id',
            'booking_code',
            'listing',
            'listing_title',
            'listing_address',
            'lessee',
            'lessee_email',
            'lessee_phone',
            'lessor_id',
            'lessor_name',

            # Даты и гости
            'check_in_date',
            'check_out_date',
            'number_of_guests',
            'total_nights',

            # Цены
            'price',
            'total_amount',

            # Информация о госте
            'guest_first_name',
            'guest_last_name',
            'guest_notes',
            'guest_phone',
            'guest_email',
            'special_requests',

            # Статусы и даты
            'status',
            'confirmed_at',
            'cancelled_at',
            'cancelled_by',
            'cancellation_reason',
            'created_at',
            'updated_at',

            # Флаги
            'is_paid',
            'is_deposit_returned',
            'is_deleted',
            'deleted_at',

            # Вычисляемые поля
            'is_active',
            'can_be_cancelled',
            'nights_remaining',
            'current_stay_progress',

            # Связанные данные
            'calendar_dates',
        ]
        read_only_fields = [
            'booking_code',
            'total_nights',
            'total_amount',
            'confirmed_at',
            'cancelled_at',
            'cancelled_by',
            'created_at',
            'updated_at',
            'status',
            'is_deleted',
            'deleted_at',
            'calendar_dates',
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания бронирования"""

    class Meta:
        model = Booking
        fields = [
            'listing',
            'check_in_date',
            'check_out_date',
            'number_of_guests',
            'guest_first_name',
            'guest_last_name',
            'guest_notes',
            'guest_phone',
            'special_requests',
        ]

    def validate(self, data):
        listing = data.get('listing')
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        guests = data.get('number_of_guests', 1)

        # Базовые проверки
        if not all([listing, check_in, check_out]):
            raise serializers.ValidationError(
                "Необходимо указать жилье, дату заезда и дату выезда"
            )

        # Проверяем даты
        if check_out <= check_in:
            raise serializers.ValidationError({
                'check_out_date': 'Дата выезда должна быть позже даты заезда'
            })

        if check_in < timezone.now().date():
            raise serializers.ValidationError({
                'check_in_date': 'Дата заезда должна быть в будущем'
            })

        # # Проверяем доступность через календарь
        # is_available = CalendarService.check_date_range_availability(
        #     listing=listing,
        #     start_date=check_in,
        #     end_date=check_out
        # )
        #
        # if not is_available:
        #     raise serializers.ValidationError({
        #         'check_in_date': 'Выбранные даты недоступны для бронирования'
        #     })
        if not data['listing'].is_available:
            raise serializers.ValidationError({
                "listing": "Объявление недоступно для бронирования"
            })

        # Есть ли пересечения с другими бронированиями?
        conflicting = Booking.objects.filter(
            listing=data['listing'],
            check_in_date__lt=data['check_out_date'],  # Начало другой брони < нашего выезда
            check_out_date__gt=data['check_in_date'],  # Конец другой брони > нашего заезда
            status__in=['confirmed', 'pending']  # Только активные брони
        ).exists()

        if conflicting:
            raise serializers.ValidationError({
                "dates": "На эти даты уже есть бронирование"
            })

        # Проверяем количество гостей
        if guests < 1:
            raise serializers.ValidationError({
                'number_of_guests': 'Количество гостей должно быть не менее 1'
            })

        if guests > listing.max_guests:
            raise serializers.ValidationError({
                'number_of_guests': f'Максимальное количество гостей: {listing.max_guests}'
            })

        # Проверяем минимальный срок проживания
        nights = (check_out - check_in).days
        if nights < listing.min_stay_days:
            raise serializers.ValidationError({
                'check_out_date': f'Минимальный срок проживания: {listing.min_stay_days} дней'
            })

        # Рассчитываем цену
        nights = (check_out - check_in).days
        base_price = listing.price * nights

        # 3. Доплата за гостей (если > 1)
        extra_charge = 0
        if guests > 1:
            extra_charge = (guests - 1) * 20 * nights  # 20 euro за доп. гостя/ночь

        total_price = base_price + extra_charge
        data['price'] = base_price  # цена без доплат
        data['total_amount'] = total_price  # итоговая сумма

        return data


class BookingUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления бронирования"""

    class Meta:
        model = Booking
        fields = [
            'guest_first_name',
            'guest_last_name',
            'guest_notes',
            'guest_phone',
            'special_requests',
        ]

    def validate(self, data):
        booking = self.instance

        # Проверяем, можно ли редактировать
        if booking.status not in [BookingStatus.PENDING.value, BookingStatus.CONFIRMED.value]:
            raise serializers.ValidationError(
                "Редактирование возможно только для бронирований со статусом PENDING или CONFIRMED"
            )

        # Проверяем, что не позже чем за 2 дня до заезда
        if booking.check_in_date - timezone.now().date() < timedelta(days=2):
            raise serializers.ValidationError(
                "Редактирование невозможно менее чем за 2 дня до заезда"
            )

        return data


class CancelBookingSerializer(serializers.Serializer):
    """Сериализатор для отмены бронирования"""

    reason = serializers.CharField(required=False, max_length=500, allow_blank=True)

    def validate(self, data):
        booking = self.context['booking']

        if not booking.can_be_cancelled:
            raise serializers.ValidationError(
                "Бронирование не может быть отменено"
            )

        return data


class ConfirmBookingSerializer(serializers.Serializer):
    """Сериализатор для подтверждения/отклонения бронирования владельцем"""

    action = serializers.ChoiceField(choices=['confirm', 'reject'])
    reason = serializers.CharField(required=False, max_length=500, allow_blank=True)


class BookingListSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для списка бронирований"""

    listing_title = serializers.CharField(source='listing.title', read_only=True)
    lessee_name = serializers.CharField(source='lessee.get_full_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'booking_code',
            'listing',
            'listing_title',
            'lessee',
            'lessee_name',
            'check_in_date',
            'check_out_date',
            'number_of_guests',
            'total_amount',
            'status',
            'created_at',
            'is_active',
            'can_be_cancelled',
        ]