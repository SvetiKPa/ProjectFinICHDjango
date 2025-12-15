from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class User(AbstractBaseUser, PermissionsMixin):
    # ROLE_CHOICES = [
    #     ('LESSOR', 'Lessor'),
    #     ('LESSEE', 'Lessee'),
    # ]

    username = models.CharField(max_length=45, unique=True)
    email = models.EmailField(_('email address'), max_length=75,
                              unique=True)  # Вот эти _ -- это элиас функции gettext_lazy().
    # Так проще воспринимать. Функция помогает правильно отображать строковые значения,
    # особенно при работающей интернационализации
    first_name = models.CharField(_("first name"), max_length=50)
    last_name = models.CharField(_("last name"), max_length=50)
    phone = models.CharField(max_length=45, null=True, blank=True)
    age = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(6), MaxValueValidator(120)],
        null=True
    )
    # role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='LESSEE')
    role = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)

    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False, verbose_name="Удалено")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата удаления")

    objects = UserManager()

    USERNAME_FIELD = "username"  # указываем какое поле будет восприниматься как юзернейм при входе в систему
    REQUIRED_FIELDS = ["email"]  # Указываем какие поля должны быть обязательными, помимо юзернейм и пароля (при создании суперпользователя)

    def __str__(self):
        return self.email

    class Meta:
        db_table = "user"
