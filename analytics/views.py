from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from users.models import Employee
from onboarding.models import OnboardingTask, EmployeeOnboarding
from vacations.models import VacationRequest
from datetime import datetime, timedelta
from django.utils import timezone

@login_required
def dashboard(request):
    """Аналитический дашборд"""
    
    today = timezone.now().date()
    month_ago = today - timedelta(days=30)
    
    # Общая статистика
    total_employees = Employee.objects.filter(is_active=True).count()
    
    # Новые сотрудники за месяц
    new_employees = Employee.objects.filter(
        hire_date__gte=month_ago,
        is_active=True
    ).count()
    
    # Статистика по отпускам
    vacations_stats = {
        'pending': VacationRequest.objects.filter(status='pending').count(),
        'approved': VacationRequest.objects.filter(status='approved').count(),
        'rejected': VacationRequest.objects.filter(status='rejected').count(),
    }
    
    # Сейчас в отпуске
    on_vacation_now = VacationRequest.objects.filter(
        status='approved',
        start_date__lte=today,
        end_date__gte=today
    ).count()
    
    # Прогресс онбординга
    total_tasks = OnboardingTask.objects.count()
    employees_progress = []
    
    for emp in Employee.objects.filter(is_active=True)[:10]:  # топ-10
        if total_tasks > 0:
            completed = EmployeeOnboarding.objects.filter(
                employee=emp, is_completed=True
            ).count()
            progress = int((completed / total_tasks) * 100)
        else:
            progress = 0
        
        employees_progress.append({
            'name': emp.name,
            'progress': progress,
            'completed': completed,
            'total': total_tasks,
        })
    
    # Сортируем по прогрессу
    employees_progress.sort(key=lambda x: x['progress'], reverse=True)
    
    context = {
        'total_employees': total_employees,
        'new_employees': new_employees,
        'vacations_stats': vacations_stats,
        'on_vacation_now': on_vacation_now,
        'employees_progress': employees_progress,
    }
    
    return render(request, 'analytics/dashboard.html', context)