from django.db import models

class SearchHistory(models.Model):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='search_history',
        verbose_name="Пользователь",
        null=True,
        blank=True
    )
    query = models.CharField(max_length=255, verbose_name="Поисковый запрос")
    filters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Фильтры поиска"
    )
    results_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество результатов"
    )
    session_key = models.CharField(
        max_length=40,
        blank=True,
        verbose_name="Ключ сессии"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата поиска")

    class Meta:
        db_table = 'search_history'
        verbose_name = 'История поиска'
        verbose_name_plural = 'История поисков'
        ordering = ['-created_at']


    def __str__(self):
        return f"Поиск: {self.query}"
