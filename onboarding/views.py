from django.db.models import Count, Q
from django.utils import timezone
from vacations.models import VacationRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from users.models import Employee
from .models import OnboardingTask, EmployeeOnboarding
import json
from datetime import datetime, timedelta


@login_required
def dashboard(request):
    """ДАШБОРД БОМБА - с реальной статистикой"""

    # Основная статистика
    total_employees = Employee.objects.filter(is_active=True).count()

    # Новые за последние 30 дней
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    new_employees = Employee.objects.filter(
        hire_date__gte=thirty_days_ago,
        is_active=True
    ).count()

    # Прогресс онбординга
    total_tasks = OnboardingTask.objects.count()

    # Сотрудники с их прогрессом
    employees_data = []
    employees = Employee.objects.filter(is_active=True)

    completed_onboarding = 0
    in_progress = 0

    for employee in employees:
        completed_tasks = EmployeeOnboarding.objects.filter(
            employee=employee,
            is_completed=True
        ).count()

        if total_tasks > 0:
            progress = int((completed_tasks / total_tasks) * 100)

            if progress == 100:
                completed_onboarding += 1
            elif progress > 0:
                in_progress += 1
        else:
            progress = 0

        employees_data.append({
            'employee': employee,
            'progress': progress,
            'completed': completed_tasks,
            'total': total_tasks,
        })

    # Сортируем по прогрессу (сначала те, у кого меньше)
    employees_data.sort(key=lambda x: x['progress'])

    # Берём топ-5 самых новых
    recent_employees = employees_data[:5]

    context = {
        'total_employees': total_employees,
        'new_employees': new_employees,
        'completed_onboarding': completed_onboarding,
        'in_progress': in_progress,
        'employees': employees_data,
        'recent_employees': recent_employees,
        'total_tasks': total_tasks,
    }

    return render(request, 'onboarding/dashboard.html', context)

@login_required
def employee_checklist(request, employee_id):
    """Чек-лист для конкретного сотрудника"""
    employee = get_object_or_404(Employee, id=employee_id)
    
    # Получаем все задачи
    tasks = OnboardingTask.objects.all()
    
    # Получаем или создаем прогресс по задачам
    checklist = []
    for task in tasks:
        progress, created = EmployeeOnboarding.objects.get_or_create(
            employee=employee,
            task=task,
            defaults={'is_completed': False}
        )
        checklist.append({
            'task': task,
            'completed': progress.is_completed,
            'progress_id': progress.id,
        })
    
    return render(request, 'onboarding/checklist.html', {
        'employee': employee,
        'checklist': checklist,
    })

@csrf_exempt
@login_required
def toggle_task(request, task_id):
    """API для отметки выполнения задачи"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            progress = get_object_or_404(EmployeeOnboarding, id=task_id)
            
            progress.is_completed = data.get('completed', False)
            if progress.is_completed:
                progress.completed_at = datetime.now()
            else:
                progress.completed_at = None
            progress.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


def api_stats(request):
    """API для живой статистики на главной"""

    total_employees = Employee.objects.filter(is_active=True).count()

    # Сотрудники в онбординге (прогресс < 100% и > 0%)
    in_onboarding = 0
    for emp in Employee.objects.filter(is_active=True):
        total_tasks = OnboardingTask.objects.count()
        if total_tasks > 0:
            completed = EmployeeOnboarding.objects.filter(
                employee=emp, is_completed=True
            ).count()
            if completed < total_tasks and completed > 0:
                in_onboarding += 1

    # Сотрудники в отпуске сейчас
    today = timezone.now().date()
    on_vacation = 0
    try:
        on_vacation = VacationRequest.objects.filter(
            status='approved',
            start_date__lte=today,
            end_date__gte=today
        ).count()
    except:
        pass  # Если модель ещё не создана

    # Завершившие онбординг
    completed_onboarding = 0
    for emp in Employee.objects.filter(is_active=True):
        total_tasks = OnboardingTask.objects.count()
        if total_tasks > 0:
            completed = EmployeeOnboarding.objects.filter(
                employee=emp, is_completed=True
            ).count()
            if completed == total_tasks:
                completed_onboarding += 1

    return JsonResponse({
        'total_employees': total_employees,
        'in_onboarding': in_onboarding,
        'on_vacation': on_vacation,
        'completed_onboarding': completed_onboarding,
    })