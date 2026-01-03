import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.forms import BooleanField
from apps.booking.enums import BookingStatus
from datetime import timedelta

from django.utils import timezone

class Booking(models.Model):

    listing = models.ForeignKey(
        'Listing',
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name="Объявление"
    )
    lessee = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="Арендатор"
    )

    check_in_date = models.DateField(verbose_name="Дата заезда")
    check_out_date = models.DateField(verbose_name="Дата выезда")

    number_of_guests = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Количество гостей"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена за ночь",
        null=False,  # обязательное поле!
        blank=False,
        validators=[MinValueValidator(0)]
    )

    total_nights = models.PositiveIntegerField(
        verbose_name="Всего ночей",
        editable=False  # Рассчитывается автоматически
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Общая сумма",
        validators=[MinValueValidator(0)],
        editable=False
    )

    # Информация о госте
    guest_first_name = models.CharField(max_length=100, verbose_name="Имя гостя")
    guest_last_name = models.CharField(max_length=100, verbose_name="Фамилия гостя")
    guest_notes = models.TextField(blank=True, verbose_name="Пожелания гостя")
    guest_phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон гостя")
    guest_email = models.EmailField(blank=True, verbose_name="Email гостя")
    special_requests = models.TextField(blank=True, verbose_name="Особые запросы")

    # Статус бронирования
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices(),
        default=BookingStatus.PENDING.value,
        verbose_name="Статус бронирования"
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата подтверждения"
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата отмены"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата завершения"
    )

    cancelled_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_bookings',
        verbose_name="Отменено пользователем"
    )

    cancellation_reason = models.TextField(
        blank=True,
        verbose_name="Причина отмены"
    )

    booking_code = models.CharField(
        max_length=36,
        unique=True,
        editable=False,
        verbose_name="Код бронирования"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_deleted = models.BooleanField(default=False, verbose_name="Удалено")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата удаления")
    is_paid = models.BooleanField(default=False, verbose_name="Оплачено")
    is_deposit_returned = models.BooleanField(default=False, verbose_name="Залог возвращен")


    class Meta:
        db_table = "booking"
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ['-created_at']

        constraints = [
            models.UniqueConstraint(
                fields=['listing', 'check_in_date', 'check_out_date', 'status'],
                condition=models.Q(status__in=['pending', 'confirmed', 'active']),
                name='unique_booking_dates'
            ),
            # Проверка дат
            models.CheckConstraint(
                condition=models.Q(check_out_date__gt=models.F('check_in_date')),
                name='check_out_after_check_in'
            ),
            # Проверка гостей
            models.CheckConstraint(
                condition=models.Q(number_of_guests__gte=1),
                name='at_least_one_guest'
            ),
        ]

    def __str__(self):
        return f"Бронирование #{self.booking_code} - {self.listing.title}"

    def save(self, *args, **kwargs):
        # Генерация кода бронирования при создании
        if not self.booking_code:
            self.booking_code = str(uuid.uuid4())

        # Рассчитываем количество ночей
        if self.check_in_date and self.check_out_date:
            self.total_nights = (self.check_out_date - self.check_in_date).days

        # Рассчитываем общую сумму
        if self.total_nights and self.price:
            self.total_amount = self.price * self.total_nights

        # Автоматически заполняем даты статусов
        if self.status == BookingStatus.CONFIRMED.value and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        elif self.status == BookingStatus.CANCELLED.value and not self.cancelled_at:
            self.cancelled_at = timezone.now()
        elif self.status == BookingStatus.COMPLETED.value and not self.completed_at:
            self.completed_at = timezone.now()

        # Автоматическое заполнение данных гостя из профиля пользователя
        if not self.guest_email and self.lessee.email:
            self.guest_email = self.lessee.email
        if not self.guest_phone and self.lessee.phone:
            self.guest_phone = self.lessee.phone
        if not self.guest_first_name and self.lessee.first_name:
            self.guest_first_name = self.lessee.first_name
        if not self.guest_last_name and self.lessee.last_name:
            self.guest_last_name = self.lessee.last_name

        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Активно ли бронирование"""
        return self.status in [
            BookingStatus.PENDING.value,
            BookingStatus.CONFIRMED.value,
            BookingStatus.ACTIVE.value
        ]

    @property
    def can_be_cancelled(self):
        """Можно ли отменить бронирование"""
        if self.status not in [BookingStatus.PENDING.value, BookingStatus.CONFIRMED.value]:
            return False

        # Можно отменить минимум за 2 дня до заезда
        cancellation_deadline = self.check_in_date - timedelta(days=2)
        return timezone.now().date() < cancellation_deadline

    @property
    def nights_remaining(self):
        """Сколько ночей осталось до заезда"""
        if self.check_in_date:
            days = (self.check_in_date - timezone.now().date()).days
            return max(days, 0)
        return 0

    @property
    def current_stay_progress(self):
        """Прогресс текущего проживания (0-100%)"""
        if self.status != BookingStatus.ACTIVE.value:
            return 0

        total_days = (self.check_out_date - self.check_in_date).days
        days_passed = (timezone.now().date() - self.check_in_date).days
        return min(int((days_passed / total_days) * 100), 100)

    def mark_as_confirmed(self, confirmed_by=None):
        """Подтвердить бронирование"""
        self.status = BookingStatus.CONFIRMED.value
        self.confirmed_at = timezone.now()
        self.save()

    def mark_as_cancelled(self, user=None, reason=""):
        """Отменить бронирование"""
        self.status = BookingStatus.CANCELLED.value
        self.cancelled_at = timezone.now()
        self.cancelled_by = user
        self.cancellation_reason = reason
        self.save()

    def mark_as_completed(self):
        """Завершить бронирование"""
        self.status = BookingStatus.COMPLETED.value
        self.completed_at = timezone.now()
        self.save()

    def get_price_breakdown(self):
        """Детализация стоимости"""
        base_price = self.price * self.total_nights
        return {
            'nights': self.total_nights,
            'price_per_night': float(self.price),
            'base_price': float(base_price),
            'cleaning_fee': float(self.cleaning_fee),
            'service_fee': float(self.service_fee),
            'deposit': float(self.deposit_amount),
            'total': float(self.total_amount),
        }

    def clean(self):
        """Валидация перед сохранением"""
        from django.core.exceptions import ValidationError

        # Проверка дат
        if self.check_in_date and self.check_out_date:
            if self.check_out_date <= self.check_in_date:
                raise ValidationError({
                    'check_out_date': 'Дата выезда должна быть позже даты заезда'
                })

            # Проверка минимального срока проживания
            if self.listing and self.total_nights < self.listing.min_stay_days:
                raise ValidationError({
                    'check_out_date': f'Минимальный срок проживания: {self.listing.min_stay_days} дней'
                })

        # Проверка количества гостей
        if self.listing and self.number_of_guests > self.listing.max_guests:
            raise ValidationError({
                'number_of_guests': f'Максимальное количество гостей: {self.listing.max_guests}'
            })

