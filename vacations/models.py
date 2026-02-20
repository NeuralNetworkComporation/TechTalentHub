from django.db import models
from users.models import Employee
from core.models import TimeStampedModel
from django.utils import timezone


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


class ApprovalRoute(models.Model):
    """Маршруты согласования заявлений"""

    REQUEST_TYPES = [
        ('vacation', 'Отпуск'),
        ('business_trip', 'Командировка'),
    ]

    ROLES = [
        ('employee', 'Сотрудник'),
        ('manager', 'Руководитель'),
        ('hr', 'HR-специалист'),
    ]

    type = models.CharField(max_length=20, choices=REQUEST_TYPES, verbose_name="Тип заявления")
    step_no = models.PositiveIntegerField(verbose_name="Номер шага")
    role = models.CharField(max_length=20, choices=ROLES, verbose_name="Роль")
    sla_days = models.PositiveIntegerField(default=1, verbose_name="Срок согласования (дней)")

    class Meta:
        unique_together = ['type', 'step_no']
        ordering = ['type', 'step_no']
        verbose_name = "Маршрут согласования"
        verbose_name_plural = "Маршруты согласования"

    def __str__(self):
        return f"{self.get_type_display()} - Шаг {self.step_no}: {self.get_role_display()} ({self.sla_days} дн.)"


class VacationRequest(TimeStampedModel):
    """Заявка на отпуск/командировку"""

    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('submitted', 'Отправлено'),
        ('in_approval', 'На согласовании'),
        ('approved', 'Утверждён'),
        ('rejected', 'Отклонён'),
    ]

    REQUEST_TYPES = [
        ('vacation', 'Отпуск'),
        ('business_trip', 'Командировка'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='vacation_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, default='vacation',
                                    verbose_name="Тип заявления")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_requests')
    approved_at = models.DateTimeField(null=True, blank=True)

    # Поля для маршрута согласования
    current_step = models.PositiveIntegerField(default=1, verbose_name="Текущий шаг")
    step_started_at = models.DateTimeField(null=True, blank=True, verbose_name="Начало текущего шага")
    step_history = models.JSONField(default=list, blank=True, verbose_name="История прохождения шагов")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Заявка на отпуск"
        verbose_name_plural = "Заявки на отпуск"

    def days_count(self):
        return (self.end_date - self.start_date).days + 1

    def get_route(self):
        """Получить маршрут согласования для текущего типа заявки"""
        return ApprovalRoute.objects.filter(type=self.request_type).order_by('step_no')

    def get_current_step_route(self):
        """Получить информацию о текущем шаге"""
        try:
            return ApprovalRoute.objects.get(
                type=self.request_type,
                step_no=self.current_step
            )
        except ApprovalRoute.DoesNotExist:
            return None

    def can_approve(self, user):
        """Проверить, может ли пользователь утвердить текущий шаг"""
        if not user.is_authenticated:
            return False

        from users.models import Employee
        try:
            employee = Employee.objects.get(user=user)
        except Employee.DoesNotExist:
            return False

        current_step_route = self.get_current_step_route()
        if not current_step_route:
            return False

        # Проверка роли
        if current_step_route.role == 'manager':
            # Проверить, что пользователь - руководитель сотрудника
            # Здесь нужна логика определения руководителя
            return employee.position and 'руководитель' in employee.position.lower()
        elif current_step_route.role == 'hr':
            # Проверить, что пользователь - HR
            return employee.position and ('hr' in employee.position.lower() or 'кадр' in employee.position.lower())
        elif current_step_route.role == 'employee':
            # Только сам сотрудник
            return employee.id == self.employee.id

        return False

    def move_to_next_step(self):
        """Перейти к следующему шагу маршрута"""
        from django.utils import timezone

        # Записываем завершённый шаг в историю
        if self.current_step > 0:
            step_info = {
                'step': self.current_step,
                'started_at': self.step_started_at.isoformat() if self.step_started_at else None,
                'ended_at': timezone.now().isoformat(),
                'approved_by': self.approved_by.id if self.approved_by else None,
            }
            # Создаём новый список, если его нет
            if not self.step_history:
                self.step_history = []
            self.step_history.append(step_info)

        # Переходим к следующему шагу
        next_step = self.current_step + 1
        route_exists = ApprovalRoute.objects.filter(
            type=self.request_type,
            step_no=next_step
        ).exists()

        if route_exists:
            self.current_step = next_step
            self.step_started_at = timezone.now()
            self.status = 'in_approval'
            return True
        else:
            # Маршрут завершён
            self.status = 'approved'
            self.current_step = 0
            self.approved_at = timezone.now()
            return False

    def approve(self, user):
        """Утвердить текущий шаг"""
        if not self.can_approve(user):
            return False, "Нет прав для утверждения"

        from users.models import Employee
        self.approved_by = Employee.objects.get(user=user)

        # Переходим к следующему шагу
        has_next = self.move_to_next_step()
        self.save()

        if has_next:
            return True, f"Заявка перешла на шаг {self.current_step}"
        else:
            return True, "Заявка полностью утверждена"

    def __str__(self):
        return f"{self.get_request_type_display()}: {self.employee.name} - {self.start_date} to {self.end_date}"

@property
def can_approve_for_current_user(self):
    """Проверка для текущего пользователя (должен передаваться из view)"""
    # Эта логика будет вызываться из view, не из шаблона
    return False