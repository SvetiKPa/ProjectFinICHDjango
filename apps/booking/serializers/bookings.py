from rest_framework import serializers
from apps.booking.models import Booking
from apps.booking.enums import BookingStatus
from django.utils import timezone
from datetime import timedelta
from apps.booking.permissions import IsLessee
from apps.booking.availability import AvailabilityService
# from apps.booking.serializers import CalendarSerializer


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
    guest_first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Обязательно для гостей. Для арендаторов заполняется автоматически"
    )
    guest_last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Обязательно для гостей. Для арендаторов заполняется автоматически"
    )
    guest_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="Обязательно для гостей. Для арендаторов заполняется автоматически"
    )
    guest_phone = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Необязательно"
    )

    class Meta:
        model = Booking
        fields = [
            'listing',
            'check_in_date',
            'check_out_date',
            'number_of_guests',
            'guest_first_name',
            'guest_last_name',
            'guest_email',
            'guest_phone',
            'guest_notes',
            'guest_phone',
            'special_requests',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request:
            is_lessee = IsLessee().has_permission(request, None)

            if is_lessee:
                # Для арендаторов: поля НЕ обязательные
                self.fields['guest_first_name'].required = False
                self.fields['guest_last_name'].required = False
                self.fields['guest_email'].required = False
            else:
                # Для гостей/других пользователей: поля ОБЯЗАТЕЛЬНЫЕ
                self.fields['guest_first_name'].required = True
                self.fields['guest_last_name'].required = True
                self.fields['guest_email'].required = True

    def validate(self, data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")

        is_lessee = IsLessee().has_permission(request, None)

        if is_lessee:
            # АРЕНДАТОР (LESSER)
            user = request.user

            # Берем данные из профиля
            data['guest_first_name'] = user.first_name or ''
            data['guest_last_name'] = user.last_name or ''
            data['guest_email'] = user.email or ''

            if not data.get('guest_phone') and hasattr(user, 'phone') and user.phone:
                data['guest_phone'] = user.phone

            # Проверяем что в профиле есть необходимые данные
            if not data['guest_first_name']:
                raise serializers.ValidationError({
                    'guest_first_name': 'Заполните имя в профиле или укажите в запросе'
                })
            if not data['guest_last_name']:
                raise serializers.ValidationError({
                    'guest_last_name': 'Заполните фамилию в профиле или укажите в запросе'
                })
            if not data['guest_email']:
                raise serializers.ValidationError({
                    'guest_email': 'Заполните email в профиле или укажите в запросе'
                })

        else:
            # ГОСТЬ или НЕАРЕНДАТОР
            # Проверяем что все обязательные поля заполнены
            if not data.get('guest_first_name'):
                raise serializers.ValidationError({
                    'guest_first_name': 'Имя гостя обязательно для бронирования'
                })
            if not data.get('guest_last_name'):
                raise serializers.ValidationError({
                    'guest_last_name': 'Фамилия гостя обязательна для бронирования'
                })
            if not data.get('guest_email'):
                raise serializers.ValidationError({
                    'guest_email': 'Email гостя обязателен для бронирования'
                })


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
        is_available, message = AvailabilityService.check_availability(
            listing, check_in, check_out
        )

        if not is_available:
            raise serializers.ValidationError({"dates": message})

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

    def create(self, validated_data):
        """Создание бронирования с учетом типа пользователя"""
        request = self.context['request']

        is_lessee = IsLessee().has_permission(request, None)

        if is_lessee:
            validated_data['lessee'] = request.user
        else:
            validated_data['lessee'] = None
        booking = super().create(validated_data)

        # Блокируем даты в календаре
        AvailabilityService.block_dates(
            listing=booking.listing,
            check_in_date=booking.check_in_date,
            check_out_date=booking.check_out_date,
            booking=booking
        )

        return booking


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


# class ConfirmBookingSerializer(serializers.Serializer):
#     """Сериализатор для подтверждения/отклонения бронирования владельцем"""
#
#     action = serializers.ChoiceField(choices=['confirm', 'reject'])
#     reason = serializers.CharField(required=False, max_length=500, allow_blank=True)


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