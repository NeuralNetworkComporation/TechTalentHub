from django.db import models
from django.contrib.auth.models import User
from core.models import TimeStampedModel


class Employee(TimeStampedModel):
    """Модель сотрудника (синхронизация с Битрикс24)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    bitrix_id = models.IntegerField(unique=True, verbose_name="ID в Битрикс24")
    name = models.CharField(max_length=255, verbose_name="Имя")
    email = models.EmailField(verbose_name="Email")
    position = models.CharField(max_length=255, blank=True, verbose_name="Должность")
    hire_date = models.DateField(null=True, blank=True, verbose_name="Дата приема")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

    def __str__(self):
        return self.name