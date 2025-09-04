from django.db import models

from users.models import User


class Post(models.Model):
    title = models.CharField(max_length=100, verbose_name="Заголовок публикации")
    content = models.TextField(verbose_name="Текст публикации")
    image = models.ImageField(
        blank=True, null=True, verbose_name="Изображение", upload_to="posts/post_image"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="posts",
        verbose_name="Автор",
        null=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата и время публикации"
    )
    is_paid = models.BooleanField(default=False, verbose_name="Публикация публична")

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title}"
