from django.db import models

class Address(models.Model):
    address = models.CharField(max_length=255, verbose_name="Улица и номер дома")
    city = models.CharField(max_length=100, verbose_name="Город")
    district = models.CharField(
        max_length=100,
        verbose_name="Район",
        blank=True
    )
    state = models.CharField(
        max_length=100,
        verbose_name="Федеральная земля"
    )
    country = models.CharField(
        max_length=100,
        verbose_name="Страна",
        default='Germany'
    )
    postal_code = models.CharField(max_length=10, verbose_name="Почтовый индекс")
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Широта"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Долгота"
    )
    class Meta:
        db_table = "address"
        ordering = ['country']


    def __str__(self):
        return f"{self.country}, {self.city}, {self.address}, {self.latitude}, {self.longitude},"
