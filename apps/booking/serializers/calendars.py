from django.utils import timezone
from rest_framework import serializers
from apps.booking.models import Listing, Calendar
from apps.booking.enums import BookingStatus, TimeSlot, AvailabilityStatus


class CalendarAvailabilityCheckSerializer(serializers.Serializer):
    """Сериализатор для проверки доступности дат"""

    listing_id = serializers.IntegerField()
    check_in_date = serializers.DateField()
    check_out_date = serializers.DateField()
    time_slot = serializers.ChoiceField(
        choices=TimeSlot.choices(),
        default=TimeSlot.WHOLE_DAY,
        required=False
    )

    def validate(self, data):
        listing_id = data['listing_id']

        try:
            listing = Listing.objects.get(id=listing_id)
        except Listing.DoesNotExist:
            raise serializers.ValidationError({
                'listing_id': 'Листинг не найден'
            })

        check_in = data['check_in_date']
        check_out = data['check_out_date']

        # Базовые проверки дат
        if check_in >= check_out:
            raise serializers.ValidationError({
                'check_out_date': 'Дата выезда должна быть позже даты заезда'
            })

        if check_in < timezone.now().date():
            raise serializers.ValidationError({
                'check_in_date': 'Дата заезда должна быть в будущем'
            })

        data['listing'] = listing
        return data
