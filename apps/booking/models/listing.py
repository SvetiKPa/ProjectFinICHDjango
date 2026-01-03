from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from apps.booking.enums import PropertyType, Status
from apps.booking.managers import SoftDeleteManager


class Listing(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание")
    address = models.ForeignKey(
        'Address',
        on_delete=models.CASCADE,
        related_name='listings',
        verbose_name='Адрес'
    )
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
    lessor = models.ForeignKey('User',
            on_delete=models.CASCADE,
            related_name='listings',
            verbose_name="Арендодатель")

    property_type = models.CharField(
        max_length=50,
        choices=PropertyType.choices(),
        default=PropertyType.HOUSE.value,
        verbose_name="Тип недвижимости"
    )
    rooms = models.PositiveIntegerField(
        verbose_name="Количество комнат",
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    bedrooms = models.PositiveIntegerField(
        verbose_name="Спальни",
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    bathrooms = models.PositiveIntegerField(
        verbose_name="Санузлы"   #TODO
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
        default=1,
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

    is_featured = models.BooleanField(
        default=False,
        verbose_name="Рекомендуемое"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices(),
        default=Status.DRAFT.value,
        verbose_name="Статус"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата публикации"
    )

    is_deleted = models.BooleanField(default=False, verbose_name="Удалено")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата удаления")

    objects = SoftDeleteManager()

    class Meta:
        db_table = "listing"
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"
        ordering = ['-created_at']

    def __str__(self):
        city_name = self.address.city if self.address else "Без адреса"
        return f"{self.title} - {city_name} ({self.price}€)"

    @property
    def city(self):
        return self.address.city if self.address else None

    @property
    def full_address(self):
        if self.address:
            return f"{self.address.city}, {self.address.street}"
        return "Адрес не указан"

    @property
    def average_rating(self):
        """Средний рейтинг из отзывов"""
        from django.db.models import Avg
        result = self.reviews.filter(is_deleted=False).aggregate(avg=Avg('rating'))
        return result['avg'] or 0

    @property
    def reviews_count(self):
        """Количество отзывов"""
        return self.reviews.filter(is_deleted=False).count()

    @property
    def views_count(self):
        """Количество просмотров"""
        if hasattr(self, 'stats'):
            return self.stats.views_count
        return self.view_history.count()

    @property
    def popularity_score(self):
        """Счет популярности для сортировки"""
        return (self.views_count * 0.5) + (self.reviews_count * 2) + (self.average_rating * 10)

    def mark_as_published(self):
        """Пометить как опубликованное"""
        from django.utils import timezone
        self.status = Status.PUBLISHED.value
        self.published_at = timezone.now()
        self.save()

    def mark_as_deleted(self):
        """Мягкое удаление"""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def increment_view(self, request=None):
        from apps.booking.models.view_history import ViewHistory
        """Увеличить счетчик просмотров"""
        # Создаем запись в истории просмотров
        view_data = {
            'listing': self,
            'session_key': request.session.session_key if request and hasattr(request, 'session') else '',
            'ip_address': request.META.get('REMOTE_ADDR') if request else None,
            'user_agent': request.META.get('HTTP_USER_AGENT', '') if request else '',
        }

        if request and request.user.is_authenticated:
            view_data['user'] = request.user

        ViewHistory.objects.create(**view_data)
