from rest_framework import serializers
from apps.booking.models import Review, Booking
from apps.booking.enums import BookingStatus


class ReviewSerializer(serializers.ModelSerializer):
    """Простой сериализатор для отзывов"""

    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'listing',
            'listing_title',
            'booking',
            'reviewer',
            'reviewer_name',
            'rating',
            'comment',
            'created_at',
        ]
        read_only_fields = ['reviewer', 'listing', 'created_at']


class CreateReviewSerializer(serializers.ModelSerializer):
    """Создание отзыва"""

    class Meta:
        model = Review
        fields = ['booking', 'rating', 'comment']

    def validate(self, data):
        booking = data['booking']
        user = self.context['request'].user

        # 1. Только арендатор может оставить отзыв
        if booking.lessee != user:
            raise serializers.ValidationError("Вы не арендатор этого бронирования")

        # 2. Только завершенное бронирование
        if booking.status != BookingStatus.COMPLETED.value:
            raise serializers.ValidationError("Отзыв можно оставить только после завершенного бронирования")

        # 3. Один отзыв на бронирование
        if Review.objects.filter(booking=booking).exists():
            raise serializers.ValidationError("На это бронирование уже есть отзыв")

        # Автоматически заполняем listing из бронирования
        data['listing'] = booking.listing
        data['reviewer'] = user

        return data
