from django.db import models


class PropertyType(models.TextChoices):
    APARTMENT = 'apartment', 'Квартира'
    HOUSE = 'house', 'Дом'
    HOTEL = 'hotel', 'Отель'
    HOSTEL = 'hostel', 'хостел'
    STUDIO = 'studio', 'Студия'
    VILLA = 'villa', 'Вилла'
    COTTAGE = 'cottage', 'Коттедж'
    TOWNHOUSE = 'townhouse', 'Таунхаус'
    PENTHOUSE = 'penthouse', 'Пентхаус'
    DUPLEX = 'duplex', 'Дуплекс'
    LOFT = 'loft', 'Лофт'


class Listing(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена",
        validators=[MinValueValidator(0)]
    )
    deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Залог",
        null=True,
        blank=True
    )
    owner = models.ForeignKey('User',
            on_delete=models.CASCADE,
            related_name='listings',
            verbose_name="Арендодатель")
    # Локация
    address = models.CharField(max_length=255, verbose_name="Улица и номер дома")
    city = models.CharField(max_length=100, verbose_name="Город")
    district = models.CharField(
        max_length=100,
        verbose_name="Район",
        blank=True
    )
    state = models.CharField(
        max_length=100,
        verbose_name="Федеральная земля",
        default='Berlin'  # или другая по умолчанию
    )
    country = models.CharField(
        max_length=100,
        verbose_name="Страна",
        default='Германия'
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

    # Характеристики недвижимости
    property_type = models.CharField(
        max_length=50,
        choices=PropertyType.choices,
        verbose_name="Тип недвижимости"
    )
    rooms = models.PositiveIntegerField(
        verbose_name="Количество комнат",
        validators=[MinValueValidator(1)]
    )
    bedrooms = models.PositiveIntegerField(
        verbose_name="Спальни",
        validators=[MinValueValidator(1)]
    )
    bathrooms = models.PositiveIntegerField(
        verbose_name="Санузлы",
        default=1,
        validators=[MinValueValidator(1)]
    )
    area_sqm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name="Площадь (м²)",
        validators=[MinValueValidator(1)]
    )

    has_kitchen = models.BooleanField(default=True, verbose_name="Кухня")
    has_balcony = models.BooleanField(default=False, verbose_name="Балкон")
    has_parking = models.BooleanField(default=False, verbose_name="Парковка")
    has_elevator = models.BooleanField(default=False, verbose_name="Лифт")
    has_furniture = models.BooleanField(default=False, verbose_name="Меблировано")
    has_internet = models.BooleanField(default=False, verbose_name="Интернет")
    pets_allowed = models.BooleanField(default=False, verbose_name="Можно с животными")
    smoking_allowed = models.BooleanField(default=False, verbose_name="Можно курить")

    # Аренда
    max_guests = models.PositiveIntegerField(
        verbose_name="Максимум гостей",
        validators=[MinValueValidator(1)]
    )
    min_stay_days = models.PositiveIntegerField(
        verbose_name="Минимальный срок (дней)",
        default=1
    )
    max_stay_days = models.PositiveIntegerField(
        verbose_name="Максимальный срок (дней)",
        null=True,
        blank=True
    )
    available_from = models.DateField(verbose_name="Доступно с")
    available_until = models.DateField(
        verbose_name="Доступно до",
        null=True,
        blank=True
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name="Доступно для аренды"
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="Опубликовано"
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Рекомендуемое"
    )
    status = models.CharField(
        max_length=20,
        choices=(
            ('draft', 'Черновик'),
            ('published', 'Опубликовано'),
            ('archived', 'В архиве'),
            ('rented', 'Сдано'),
        ),
        default='draft',
        verbose_name="Статус"
    )


    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата публикации"
    )
    # views_count = models.PositiveIntegerField(
    #     default=0,
    #     verbose_name="Количество просмотров"
    # )

    # listingimage = models. img       #TODO

    is_deleted = models.BooleanField(default=False, verbose_name="Удалено")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата удаления")


    class Meta:
        db_table = "listing"
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.city} ({self.price}€)"