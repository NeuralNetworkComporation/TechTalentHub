from django.db import models
from users.models import Employee
from core.models import TimeStampedModel


class OnboardingTask(models.Model):
    """Шаблон задачи для чек-листа"""
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        ordering = ['order']
        verbose_name = "Задача онбординга"
        verbose_name_plural = "Задачи онбординга"

    def __str__(self):
        return self.title


class EmployeeOnboarding(TimeStampedModel):
    """Прогресс сотрудника по онбордингу"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='onboarding')
    task = models.ForeignKey(OnboardingTask, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False, verbose_name="Выполнено")
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['employee', 'task']
        verbose_name = "Прогресс онбординга"
        verbose_name_plural = "Прогресс онбординга"

    def __str__(self):
        return f"{self.employee.name} - {self.task.title}"