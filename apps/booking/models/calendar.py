from django.db import models
from apps.booking.enums import AvailabilityStatus, TimeSlot
# Заезд (check-in) → после 14:00
# Выезд (check-out) → до 10:00

class Calendar(models.Model):
    listing = models.ForeignKey('Listing', on_delete=models.CASCADE, related_name='calendars',
                                null=True,
                                blank=True)
    target_date = models.DateField(verbose_name="Дата")
    is_available = models.BooleanField(default=True, verbose_name="Доступно")    # Временной слот
    # time_slot = models.SmallIntegerField(
    #     choices=TimeSlot.choices(),
    #     default=TimeSlot.WHOLE_DAY,
    #     verbose_name="Время"
    # )
    booking = models.ForeignKey(
        'Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calendar_days'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_deleted = models.BooleanField(default=False, verbose_name="Удалено")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата удаления")

    class Meta:
        db_table = "calendar"
        verbose_name = "Запись календаря"
        verbose_name_plural = "Записи календаря"
        unique_together = ['listing', 'target_date']
        ordering = ['target_date']

    def __str__(self):
        status = "Свободно" if self.is_available else "Занято"
        return f"{self.target_date}: {status}"