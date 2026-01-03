from django.db import models

class ListingImage(models.Model):
    listing = models.ForeignKey(
        'Listing',
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Объявление"
    )
    # image = models.ImageField(
    #     upload_to='listings/%Y/%m/%d/',
    #     verbose_name="Изображение"
    # )
    is_main = models.BooleanField(default=False, verbose_name="Основное фото")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Фотография объявления"
        verbose_name_plural = "Фотографии объявлений"
        ordering = ['created_at']

    def __str__(self):
        return f"Фото для {self.listing.title}"
