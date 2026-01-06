from rest_framework import serializers
from apps.booking.models import Review, Booking
from apps.booking.enums import BookingStatus


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_address = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'listing',
            'listing_title',
            'listing_address',
            'booking',
            'reviewer',
            'reviewer_name',
            'rating',
            'comment',
            'created_at',
        ]
        read_only_fields = ['reviewer', 'listing', 'created_at']

    def get_listing_address(self, obj):
        if obj.listing and hasattr(obj.listing, 'address'):
            address = obj.listing.address
            if address:
                parts = []
                if hasattr(address, 'address') and address.address:
                    parts.append(address.address)
                if hasattr(address, 'city') and address.city:
                    parts.append(address.city)
                return ", ".join(parts)
        return "Адрес не указан"


class CreateReviewSerializer(serializers.ModelSerializer):
    """Создание отзыва"""

    class Meta:
        model = Review
        fields = ['booking', 'rating', 'comment']

    def validate(self, data):
        booking = data['booking']
        user = self.context['request'].user

        if booking.lessee != user:
            raise serializers.ValidationError("Вы не арендатор этого бронирования")

        if booking.status != BookingStatus.COMPLETED.value:
            raise serializers.ValidationError("Отзыв можно оставить только после завершенного бронирования")

        # 3. Один отзыв на бронирование
        if Review.objects.filter(booking=booking).exists():
            raise serializers.ValidationError("На это бронирование уже есть отзыв")

        data['listing'] = booking.listing
        data['reviewer'] = user

        return data
