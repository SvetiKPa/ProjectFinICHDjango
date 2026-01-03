from django.db import models


class ViewHistory(models.Model):
    listing = models.ForeignKey(
        'Listing',
        on_delete=models.CASCADE,
        related_name='view_history',
        verbose_name="Объявление"
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='view_history',
        verbose_name="Пользователь"
    )
    session_key = models.CharField(
        max_length=40,
        blank=True,
        verbose_name="Ключ сессии"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP адрес"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата просмотра")

    class Meta:
        db_table = 'view_history'
        verbose_name = 'История просмотра'
        verbose_name_plural = 'История просмотров'
        ordering = ['-created_at']

    def __str__(self):
        return f"Просмотр: {self.listing.title}"