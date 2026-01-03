from rest_framework import serializers
from apps.booking.models import Listing, Address


class ListingSerializer(serializers.ModelSerializer):
    lessor = serializers.ReadOnlyField(source='lessor.username')
    address = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        required=True
    )
    city = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'address', 'city',
            'property_type', 'price', 'rooms', 'bedrooms',
            'bathrooms', 'area_sqm', 'max_guests', 'available_from',
            'lessor', 'published_at'
        ]
        read_only_fields = ['id', 'published_at', 'lessor']

    def get_city(self, obj):
        """Получаем город из связанного адреса"""
        if obj.address and hasattr(obj.address, 'city'):
            return obj.address.city
        return None


class ListingDetailedSerializer(serializers.ModelSerializer):
    lessor = serializers.ReadOnlyField(source='lessor.username')
    lessor_email = serializers.ReadOnlyField(source='lessor.email')
    lessor_phone = serializers.ReadOnlyField(source='lessor.phone')

    # Детали адреса
    address_display = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()

    # Координаты
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    coordinates = serializers.SerializerMethodField()
    has_coordinates = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = '__all__'
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'published_at',
            'lessor',
            'lessor_email',
            'lessor_phone',
        ]

    def get_city(self, obj):
        if obj.address and hasattr(obj.address, 'city'):
            return obj.address.city
        return None

    def get_address_display(self, obj):
        if obj.address:
            return f"{obj.address.city}, {obj.address.address}"
        return None

    def get_full_address(self, obj):
        """Полный адрес в виде словаря"""
        if obj.address:
            return {
                'address': obj.address.address,
                'city': obj.address.city,
                'postal_code': getattr(obj.address, 'postal_code', ''),
                'country': getattr(obj.address, 'country', ''),
                'latitude': getattr(obj.address, 'latitude', None),
                'longitude': getattr(obj.address, 'longitude', None),
                'district': getattr(obj.address, 'district', ''),
                'state': getattr(obj.address, 'state', '')
            }
        return None

    def get_latitude(self, obj):
        if obj.address and obj.address.latitude:
            return float(obj.address.latitude)
        return None

    def get_longitude(self, obj):
        if obj.address and obj.address.longitude:
            return float(obj.address.longitude)
        return None

    def get_coordinates(self, obj):
        """Формат для большинства карт (Google Maps, Yandex Maps)"""
        if obj.address and obj.address.latitude and obj.address.longitude:
            return {
                'lat': float(obj.address.latitude),
                'lng': float(obj.address.longitude)
            }
        return None

    def get_has_coordinates(self, obj):
        """Проверка, есть ли координаты"""
        return bool(
            obj.address and
            obj.address.latitude and
            obj.address.longitude
        )


class ListingUpdateSerializer(serializers.ModelSerializer):
    address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        source='address',
        write_only=True,
        required=False
    )

    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'address_id', 'price',
            'property_type', 'rooms', 'bedrooms', 'bathrooms',
            'area_sqm', 'max_guests', 'available_from',
            'is_available', 'deposit', 'min_stay_days', 'max_stay_days',
            'has_kitchen', 'has_balcony', 'has_parking', 'has_elevator',
            'has_furniture', 'has_internet', 'pets_allowed', 'smoking_allowed'
        ]
