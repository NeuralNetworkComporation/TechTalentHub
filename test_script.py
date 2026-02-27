from users.models import Employee
from django.contrib.auth.models import User
from vacations.models import VacationRequest
from django.utils import timezone
from datetime import timedelta

# 1. Найдём сотрудников (смотрим всех)
print("ВСЕ СОТРУДНИКИ:")
for emp in Employee.objects.all():
    print(f"ID: {emp.id}, Имя: {emp.name}")

# 2. Найдём конкретных
ivanov = Employee.objects.filter(name__icontains='Иван').first()
petrov = Employee.objects.filter(name__icontains='Петр').first()
anna = Employee.objects.filter(name__icontains='Анна').first()

print(f"\nИванов: {ivanov.name if ivanov else 'Не найден'}")
print(f"Петров: {petrov.name if petrov else 'Не найден'}")
print(f"Анна: {anna.name if anna else 'Не найден'}")

if ivanov and petrov:
    # 3. Назначаем руководителя
    ivanov.manager = petrov
    ivanov.save()
    print(f"✅ Руководитель Иванова: {ivanov.manager.name}")

    # 4. Создаём заявку
    new_request = VacationRequest.objects.create(
        employee=ivanov,
        request_type='vacation',
        start_date=timezone.now().date() + timedelta(days=5),
        end_date=timezone.now().date() + timedelta(days=12),
        comment='Тестовая заявка',
        status='submitted',
        current_step=1,
        step_started_at=timezone.now(),
    )
    print(f"✅ Создана заявка #{new_request.id}")
else:
    print("❌ Не все сотрудники найдены")