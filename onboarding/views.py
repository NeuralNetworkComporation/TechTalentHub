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
    """Дашборд HR с прогрессом новичков"""
    # Получаем новых сотрудников (принятых за последние 30 дней)
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    
    new_employees = Employee.objects.filter(
        hire_date__gte=thirty_days_ago,
        is_active=True
    ).order_by('-hire_date')
    
    # Считаем прогресс для каждого
    employees_data = []
    for employee in new_employees:
        total_tasks = OnboardingTask.objects.count()
        completed_tasks = EmployeeOnboarding.objects.filter(
            employee=employee,
            is_completed=True
        ).count()
        
        progress = 0
        if total_tasks > 0:
            progress = int((completed_tasks / total_tasks) * 100)
        
        employees_data.append({
            'employee': employee,
            'progress': progress,
            'completed': completed_tasks,
            'total': total_tasks,
        })
    
    return render(request, 'onboarding/dashboard.html', {
        'employees': employees_data,
    })

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