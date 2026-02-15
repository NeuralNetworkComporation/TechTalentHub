from django.db import models
from users.models import Employee
from core.models import TimeStampedModel


class VacationBalance(TimeStampedModel):
    """Баланс отпусков сотрудника"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='vacation_balances')
    year = models.IntegerField(verbose_name="Год")
    total_days = models.FloatField(default=28, verbose_name="Всего дней")
    used_days = models.FloatField(default=0, verbose_name="Использовано дней")

    class Meta:
        unique_together = ['employee', 'year']
        verbose_name = "Баланс отпуска"
        verbose_name_plural = "Балансы отпусков"

    def remaining_days(self):
        return self.total_days - self.used_days

    def __str__(self):
        return f"{self.employee.name} - {self.year}: {self.remaining_days()} дней"


class VacationRequest(TimeStampedModel):
    """Заявка на отпуск"""
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('pending', 'На согласовании'),
        ('approved', 'Утвержден'),
        ('rejected', 'Отклонен'),
        ('cancelled', 'Отменен'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='vacation_requests')
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_requests')
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Заявка на отпуск"
        verbose_name_plural = "Заявки на отпуск"

    def days_count(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"{self.employee.name} - {self.start_date} to {self.end_date}"