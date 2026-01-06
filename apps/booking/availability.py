from datetime import timedelta
from django.utils import timezone
from apps.booking.models import Calendar

class AvailabilityService:

    @staticmethod
    def check_availability(listing, check_in_date, check_out_date):
        """
        Проверяет доступность дат с учетом правила "выезд до 10, заезд после 14"
        Пример:
        - check_in_date = 15 декабря (заезд после 14:00 15-го)
        - check_out_date = 20 декабря (выезд до 10:00 20-го)
        - Заняты даты: 15, 16, 17, 18, 19 (5 ночей)
        - Дата 20 декабря свободна для следующего гостя
        """

        # 1. Базовые проверки
        if check_in_date >= check_out_date:
            return False, "Дата выезда должна быть позже даты заезда"

        if check_in_date < timezone.now().date():
            return False, "Дата заезда должна быть в будущем"

        # 2. Проверяем календарь
        dates_to_check = []
        current_date = check_in_date

        while current_date < check_out_date:
            dates_to_check.append(current_date)
            current_date += timedelta(days=1)

        # 3. Проверяем каждую дату в календаре
        for date in dates_to_check:
            try:
                calendar_entry = Calendar.objects.get(
                    listing=listing,
                    target_date=date
                )
                if not calendar_entry.is_available:
                    return False, f"Дата {date} занята"
            except Calendar.DoesNotExist:
                Calendar.objects.create(
                    listing=listing,
                    target_date=date,
                    is_available=True
                )

        return True, "Даты доступны"

    @staticmethod
    def block_dates(listing, check_in_date, check_out_date, booking):
        """
        Блокирует даты в календаре при создании бронирования
        """
        current_date = check_in_date

        while current_date < check_out_date:
            Calendar.objects.update_or_create(
                listing=listing,
                target_date=current_date,
                defaults={
                    'is_available': False,
                    'booking': booking
                }
            )
            current_date += timedelta(days=1)

    @staticmethod
    def free_dates(listing, check_in_date, check_out_date):
        """
        Освобождает даты в календаре при отмене бронирования
        """
        Calendar.objects.filter(
            listing=listing,
            target_date__gte=check_in_date,
            target_date__lt=check_out_date
        ).update(is_available=True, booking=None)
