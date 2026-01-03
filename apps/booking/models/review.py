from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Review(models.Model):
    listing = models.ForeignKey(
        'Listing',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Объявление"
    )

    # OneToOne с Booking - один отзыв на одно бронирование
    booking = models.OneToOneField(
        'Booking',
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name="Бронирование",
        unique=True
    )

    # Кто оставил отзыв - арендатор (lessee)
    reviewer = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Автор отзыва"
    )

    rating = models.FloatField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Рейтинг"
    )

    comment = models.TextField(verbose_name="Комментарий")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        db_table = 'review'
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

        # Автоматическая проверка: один отзыв на бронирование
        constraints = [
            models.UniqueConstraint(
                fields=['booking'],
                name='unique_review_per_booking'
            ),
        ]

    def __str__(self):
        return f"Отзыв на {self.listing.title} ({self.rating}/10)"
