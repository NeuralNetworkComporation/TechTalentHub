from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.models import Employee
from .models import VacationRequest, VacationBalance
from datetime import datetime, date
from django.utils import timezone
from django.http import JsonResponse


@login_required
def vacation_list(request):
    """Список заявок на отпуск"""
    # Для HR показываем все заявки, для сотрудника - только свои
    if request.user.is_staff:
        vacations = VacationRequest.objects.all().order_by('-created_at')
    else:
        # Пытаемся найти сотрудника по связанному пользователю
        try:
            employee = Employee.objects.get(user=request.user)
            vacations = VacationRequest.objects.filter(employee=employee).order_by('-created_at')
        except Employee.DoesNotExist:
            vacations = []

    return render(request, 'vacations/list.html', {
        'vacations': vacations
    })


@login_required
def vacation_create(request):
    """Создание новой заявки на отпуск"""
    if request.method == 'POST':
        # Получим данные из формы
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        comment = request.POST.get('comment', '')

        # Найдём сотрудника
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            messages.error(request, 'Сотрудник не найден')
            return redirect('vacation_list')

        # Создаём заявку
        vacation = VacationRequest.objects.create(
            employee=employee,
            start_date=start_date,
            end_date=end_date,
            comment=comment,
            status='pending'
        )

        messages.success(request, 'Заявка на отпуск создана и отправлена на согласование')
        return redirect('vacation_list')

    return render(request, 'vacations/create.html')


@login_required
def vacation_detail(request, pk):
    """Детальная страница заявки"""
    vacation = get_object_or_404(VacationRequest, pk=pk)
    return render(request, 'vacations/detail.html', {
        'vacation': vacation
    })


@login_required
def vacation_calendar(request):
    """Календарь отпусков"""
    return render(request, 'vacations/calendar.html')


@login_required
def vacation_approve(request, pk):
    """Утверждение заявки (только для HR)"""
    if not request.user.is_staff:
        messages.error(request, 'Нет прав для этого действия')
        return redirect('vacation_list')

    vacation = get_object_or_404(VacationRequest, pk=pk)
    vacation.status = 'approved'
    vacation.approved_at = timezone.now()
    vacation.save()

    messages.success(request, f'Заявка на отпуск для {vacation.employee.name} утверждена')
    return redirect('vacation_detail', pk=pk)


@login_required
def vacation_reject(request, pk):
    """Отклонение заявки (только для HR)"""
    if not request.user.is_staff:
        messages.error(request, 'Нет прав для этого действия')
        return redirect('vacation_list')

    vacation = get_object_or_404(VacationRequest, pk=pk)
    vacation.status = 'rejected'
    vacation.save()

    messages.success(request, f'Заявка на отпуск для {vacation.employee.name} отклонена')
    return redirect('vacation_detail', pk=pk)


def calendar_api(request):
    """API для календаря отпусков (возвращает события в формате FullCalendar)"""
    vacations = VacationRequest.objects.filter(status='approved')

    events = []
    for vac in vacations:
        events.append({
            'title': f'Отпуск: {vac.employee.name}',
            'start': vac.start_date.isoformat(),
            'end': (vac.end_date + timedelta(days=1)).isoformat(),  # +1 день для FullCalendar
            'color': '#2fc6f6',
            'textColor': 'white',
            'url': f'/vacations/{vac.id}/',
            'description': vac.comment,
        })

    return JsonResponse(events, safe=False)