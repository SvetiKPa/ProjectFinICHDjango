from django.db import models
from apps.booking.enums import AvailabilityStatus, TimeSlot


class Calendar(models.Model):
    listing = models.ForeignKey('Listing', on_delete=models.CASCADE, related_name='calenders',
                                null=True,
                                blank=True,
        verbose_name="Объявление")
    target_date = models.DateField(verbose_name="Дата")
    availability = models.SmallIntegerField(
        choices=AvailabilityStatus.choices(),
        default=AvailabilityStatus.FREE,
        verbose_name="Статус"
    )
    # Временной слот
    time_slot = models.SmallIntegerField(
        choices=TimeSlot.choices(),
        default=TimeSlot.WHOLE_DAY,
        verbose_name="Время"
    )

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
        # Уникальность: одна запись на дату+время для каждого объявления
        unique_together = ['listing', 'target_date', 'time_slot']
        ordering = ['target_date', 'time_slot']

    def __str__(self):
        return f"{self.target_date} ({self.get_time_slot_display()}): {self.get_availability_display()}"

    @property
    def is_available(self):
        return self.availability == AvailabilityStatus.FREE

    @property
    def human_readable_status(self):
        if self.availability == AvailabilityStatus.FREE:
            return f"Свободно ({self.get_time_slot_display()})"
        else:
            return f"Занято ({self.get_time_slot_display()})"