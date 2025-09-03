from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = None
    phone = models.CharField(
        unique=True,
        verbose_name="Телефон",
        blank=True,
        null=True,
        help_text="Введите номер телефона",
    )
    image = models.ImageField(
        upload_to="users/", verbose_name="Изображение", blank=True, null=True
    )
    has_paid_subscription = models.BooleanField(default=False, verbose_name="Подписка")

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.phone


class Payment(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="payments",
        null=True,
        blank=True,
    )
    amount = models.PositiveIntegerField(
        verbose_name="Платеж", help_text="Сумма платежа"
    )
    session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID сессии",
        help_text="Укажите ID сессии",
    )
    link = models.URLField(
        max_length=400,
        blank=True,
        null=True,
        verbose_name="Ссылка на оплату",
        help_text="Укажите ссылка на оплату",
    )

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"

    def __str__(self):
        if self.user:
            return f"Платеж {self.amount} руб. - {self.user.phone}"
        return f"Платеж {self.amount} руб. - Аноним"
