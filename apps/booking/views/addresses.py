from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.booking.models import Address
from apps.booking.serializers import AddressSerializer, AddressDetailSerializer


class AddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления адресами.
    """
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # Фильтрация и поиск
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['city', 'state', 'country', 'district']
    search_fields = ['address', 'city', 'district', 'postal_code']
    ordering_fields = ['city', 'address', 'created_at']
    ordering = ['city', 'address']

    def get_serializer_class(self):
        """Используем краткий сериализатор для списка"""
        if self.action == 'list':
            return AddressDetailSerializer
        return AddressSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        city_filter = self.request.query_params.get('city')
        if city_filter:
            queryset = queryset.filter(city__iexact=city_filter)

        country_filter = self.request.query_params.get('country')
        if country_filter:
            queryset = queryset.filter(country__iexact=country_filter)

        return queryset.order_by('city', 'address')
