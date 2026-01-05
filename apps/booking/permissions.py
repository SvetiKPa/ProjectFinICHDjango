from rest_framework import permissions
from apps.booking.enums import BookingStatus
from django.utils import timezone
from datetime import timedelta


class IsLessor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'lessor'


class IsLessee(permissions.BasePermission):
   def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'lessee'


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = None

        if hasattr(obj, 'lessee'):
            owner = obj.lessee
        elif hasattr(obj, 'reviewer'):
            owner = obj.reviewer
        elif hasattr(obj, 'lessor'):
            owner = obj.lessor
            if owner and getattr(owner, 'role', None) != 'lessor':
                return False
        elif hasattr(obj, 'listing') and hasattr(obj.listing, 'lessor'):
            owner = obj.listing.lessor
            if owner and getattr(owner, 'role', None) != 'lessor':
                return False

        # Сравниваем с текущим пользователем
        return owner == request.user if owner else False


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
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
