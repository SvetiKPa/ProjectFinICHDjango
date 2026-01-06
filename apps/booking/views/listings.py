from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from apps.booking.permissions import IsOwnerOrReadOnly, IsLessor
from apps.booking.models import Listing
from apps.booking.serializers import ListingUpdateSerializer,ListingSerializer, ListingDetailedSerializer
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from django.db.models import Q

# ViewSet  для работы с объявлениями.

class ListingViewSet(ModelViewSet):
    queryset = Listing.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'rooms',
        'bedrooms',
        'property_type',
        'has_kitchen',
        'has_parking',
        'pets_allowed',
        'is_available',
    ]

    search_fields = [
        'title',
        'description',
        'address__state',
        'address__district',
        'address__address',
        'address__city'
    ]
    ordering_fields = ['price', 'created_at', 'updated_at', 'area_sqm', 'rating', 'published_at']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsLessor()]
        elif self.action in ['update', 'partial_update', 'destroy',
                           'toggle_availability', 'publish']:
            return [IsAuthenticated(), IsLessor(), IsOwnerOrReadOnly()]
        elif self.action == 'my':
            # /my/ доступен любому авторизованному (покажет свои объявления если есть)
            return [IsAuthenticated()]
        else:  # list, retrieve
            return [AllowAny()]

    def get_serializer_class(self):
        if self.action in ['retrieve', 'my']:
            return ListingDetailedSerializer
        elif self.action in ('create', 'list'):
            return ListingSerializer
        else:  # update, partial_update
            return ListingUpdateSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Listing.objects.select_related('address', 'lessor').filter(
            is_deleted=False
        )
        if self.action == 'my':
            return Listing.objects.select_related('address', 'lessor').filter(
                lessor=user,
                is_deleted=False
            )

        # (/listings/)
        # Неавторизованные видят только опубликованные
        if not user.is_authenticated:
            queryset = queryset.filter(
                status='published',
                is_available=True
            )
        else:
            # Для авторизованных пользователей
            if hasattr(user, 'role'):
                if user.role == 'lessor':
                    # Арендодатели: свои все + чужие опубликованные и доступные
                    queryset = queryset.filter(
                        Q(lessor=user) |  # все свои
                        Q(status='published', is_available=True)  # чужие опубликованные
                    )
                else:
                    # Арендаторы: только опубликованные
                    queryset = queryset.filter(
                        status='published',
                        is_available=True
                    )
            else:
                # Если у пользователя нет role
                queryset = queryset.filter(
                    status='published',
                    is_available=True
                )

        return self._apply_filters(queryset)

    def _apply_filters(self, queryset):
        params = self.request.query_params
        user = self.request.user
        # Диапазон комнат
        min_rooms = params.get('min_rooms')
        max_rooms = params.get('max_rooms')
        if min_rooms:
            queryset = queryset.filter(rooms__gte=int(min_rooms))
        if max_rooms:
            queryset = queryset.filter(rooms__lte=int(max_rooms))

        # Диапазон цены
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=float(min_price))
        if max_price:
            queryset = queryset.filter(price__lte=float(max_price))

        min_guests = params.get('min_guests')
        max_guests = params.get('max_guests')
        if min_guests:
            queryset = queryset.filter(max_guests__gte=int(min_guests))
        if max_guests:
            queryset = queryset.filter(max_guests__lte=int(max_guests))

        # Город
        city = params.get('city')
        if city:
            queryset = queryset.filter(
                Q(address__city__iexact=city) |
                Q(address__city__icontains=city)
            )

        # Район
        district = params.get('district')
        if district:
            queryset = queryset.filter(address__district__icontains=district)
        #Фед.земля
        state = params.get('state')
        if state:
            queryset = queryset.filter(address__state__icontains=state)

        # Минимальная площадь
        min_area = params.get('min_area')
        max_area = params.get('max_area')
        if min_area:
            queryset = queryset.filter(area_sqm__gte=float(min_area))
        if max_area:
            queryset = queryset.filter(area_sqm__lte=float(max_area))

        return queryset

    def perform_create(self, serializer):
        """При создании автоматически назначаем владельца"""
        serializer.save(lessor=self.request.user)


    @action(detail=False, methods=['get'])
    def my(self, request):
        """
        Получить объявления текущего пользователя.
        GET /api/v1/listings/my/
        """
        listings = self.get_queryset()
        # Фильтрация по статусу
        status_filter = request.query_params.get('status')
        if status_filter:
            listings = listings.filter(status=status_filter)

        listings = self.filter_queryset(listings)
        if 'ordering' not in request.query_params:
            listings = listings.order_by('-created_at')

        # Пагинация
        page = self.paginate_queryset(listings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        """
        Включить/выключить доступность объявления.
        POST /api/v1/listings/{id}/toggle_availability/
        """
        listing = self.get_object()

        listing.is_available = not listing.is_available
        listing.save()

        return Response({
            'status': 'success',
            'message': f'Доступность изменена на {"доступно" if listing.is_available else "недоступно"}',
            'is_available': listing.is_available
        })

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """
        Опубликовать объявление.
        POST /api/listings/{id}/publish/
        """
        listing = self.get_object()
        listing.mark_as_published()    #models
        # listing.save()

        return Response({
            'status': 'success',
            'message': 'Объявление опубликовано',
            'published_at': listing.published_at
        })


