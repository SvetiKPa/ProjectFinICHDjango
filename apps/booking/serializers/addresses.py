from rest_framework import serializers
from apps.booking.models import Address


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id',
            'address',  # Улица и номер дома
            'city',
            'district',
            'state',
            'country',
            'postal_code',
            'latitude',
            'longitude'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if latitude and (latitude < -90 or latitude > 90):
            raise serializers.ValidationError({
                'latitude': 'Широта должна быть в диапазоне от -90 до 90'
            })

        if longitude and (longitude < -180 or longitude > 180):
            raise serializers.ValidationError({
                'longitude': 'Долгота должна быть в диапазоне от -180 до 180'
            })

        return data


class AddressDetailSerializer(serializers.ModelSerializer):
    """Краткий сериализатор для выпадающих списков"""
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = ['id', 'display_name', 'city', 'address']
        read_only_fields = ['id', 'display_name']

    def get_display_name(self, obj):
        return f"{obj.city}, {obj.address}"
