from rest_framework import permissions
from apps.booking.enums import BookingStatus
from django.utils import timezone
from datetime import timedelta


class IsLessor(permissions.BasePermission):
    """Только арендодатели (lessor)"""

    def has_permission(self, request, view):
        # Проверяем что пользователь авторизован и его роль lessor
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'lessor'


class IsLessee(permissions.BasePermission):
    """Только арендаторы (lessee)"""

    def has_permission(self, request, view):
        # Проверяем что пользователь авторизован и его роль lessee
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'lessee'


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Универсальный пермишен: чтение всем, запись - только владельцу.
    Дополнительно проверяет что владелец объявления - lessor.
    """

    def has_object_permission(self, request, view, obj):
        # Разрешаем чтение всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # Для НЕ-SAFE методов (POST, PUT, PATCH, DELETE):

        # Определяем владельца в зависимости от типа объекта
        owner = None

        if hasattr(obj, 'lessee'):
            # Для Booking: владелец - lessee (арендатор)
            owner = obj.lessee
        elif hasattr(obj, 'reviewer'):
            # Для Review: владелец - reviewer (автор отзыва)
            owner = obj.reviewer
        elif hasattr(obj, 'lessor'):
            # Для Listing: владелец - lessor (арендодатель)
            owner = obj.lessor
            # Дополнительная проверка: для объявлений владелец должен быть lessor
            if owner and getattr(owner, 'role', None) != 'lessor':
                return False
        elif hasattr(obj, 'listing') and hasattr(obj.listing, 'lessor'):
            # Для Calendar и других связанных с листингом: владелец листинга
            owner = obj.listing.lessor
            # Тоже проверяем что владелец - lessor
            if owner and getattr(owner, 'role', None) != 'lessor':
                return False

        # Сравниваем с текущим пользователем
        return owner == request.user if owner else False


class IsOwner(permissions.BasePermission):
    """Строгий пермишен: только владелец (без прав на чтение)"""

    def has_object_permission(self, request, view, obj):
        # Для всех запросов проверяем владельца
        owner = None

        if hasattr(obj, 'lessee'):
            owner = obj.lessee
        elif hasattr(obj, 'reviewer'):
            owner = obj.reviewer
        elif hasattr(obj, 'lessor'):
            owner = obj.lessor
        elif hasattr(obj, 'listing') and hasattr(obj.listing, 'lessor'):
            owner = obj.listing.lessor

        return owner == request.user if owner else False


class CanCancelBooking(permissions.BasePermission):
    """Специальный пермишен для отмены бронирования с проверкой условий"""

    def has_object_permission(self, request, view, obj):
        # 1. Только lessee (арендатор)
        if obj.lessee != request.user:
            return False

        # 2. Только определенные статусы
        if obj.status not in [BookingStatus.PENDING.value, BookingStatus.CONFIRMED.value]:
            return False

        # 3. Только до определенной даты (за 2 дня)
        cancellation_deadline = obj.check_in_date - timedelta(days=2)
        return timezone.now().date() < cancellation_deadline
