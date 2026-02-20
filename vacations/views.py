from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.models import Employee
from .models import VacationRequest, VacationBalance, ApprovalRoute
from datetime import datetime, date
from django.utils import timezone
from django.db.models import Avg, Count, Q, F, ExpressionWrapper, fields
from django.db.models.functions import Extract
from datetime import timedelta
import csv
import json
from django.http import JsonResponse, HttpResponse


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
        request_type = request.POST.get('request_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        comment = request.POST.get('comment', '')

        # Найдём сотрудника, связанного с текущим пользователем
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            messages.error(request, 'Ваш профиль не связан с сотрудником. Обратитесь к администратору.')
            return redirect('vacations:list')

        # Создаём заявку
        from django.utils import timezone
        vacation = VacationRequest.objects.create(
            employee=employee,
            request_type=request_type,
            start_date=start_date,
            end_date=end_date,
            comment=comment,
            status='submitted',
            current_step=1,
            step_started_at=timezone.now(),
        )

        messages.success(request, f'Заявка #{vacation.id} создана и отправлена на согласование')
        return redirect('vacations:list')

    return render(request, 'vacations/create.html')


@login_required
def vacation_detail(request, pk, vacation=None):
    """Детальная страница заявки"""
    context = {
        'vacation': vacation,
    }
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
        return redirect('vacations:list')  # ИСПРАВЛЕНО: было 'vacation_list'

    vacation = get_object_or_404(VacationRequest, pk=pk)
    vacation.status = 'approved'
    vacation.approved_at = timezone.now()
    vacation.save()

    messages.success(request, f'Заявка #{vacation.id} утверждена')
    return redirect('vacations:detail', pk=pk)


@login_required
def vacation_reject(request, pk):
    """Отклонение заявки (только для HR)"""
    if not request.user.is_staff:
        messages.error(request, 'Нет прав для этого действия')
        return redirect('vacations:list')

    vacation = get_object_or_404(VacationRequest, pk=pk)
    vacation.status = 'rejected'
    vacation.save()

    messages.success(request, f'Заявка #{vacation.id} отклонена')
    return redirect('vacations:detail', pk=pk)


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


def report_duration(request, self=None):
    """Отчёт по длительности согласования заявок"""

    # Базовый queryset
    queryset = VacationRequest.objects.all()

    # Фильтры (из ТЗ)
    period_start = request.GET.get('period_start')
    period_end = request.GET.get('period_end')
    request_type = request.GET.get('type')
    status = request.GET.get('status')

    if period_start:
        queryset = queryset.filter(created_at__date__gte=period_start)
    if period_end:
        queryset = queryset.filter(created_at__date__lte=period_end)
    if request_type:
        queryset = queryset.filter(request_type=request_type)
    if status:
        queryset = queryset.filter(status=status)

    # Расчёт длительности согласования (для утверждённых заявок)
    approved_requests = queryset.filter(status='approved', approved_at__isnull=False)

    durations = []
    for req in approved_requests:
        if req.approved_at and req.created_at:
            duration = (req.approved_at - req.created_at).total_seconds() / 86400  # в днях
            durations.append({
                'id': req.id,
                'type': req.get_request_type_display(),
                'employee': req.employee.name,
                'created_at': req.created_at,
                'approved_at': req.approved_at,
                'duration_days': round(duration, 2),
                'sla_days': self._calculate_sla(req),
                'overdue': duration > self._calculate_sla(req)
            })

    # Статистика
    if durations:
        avg_duration = sum(d['duration_days'] for d in durations) / len(durations)
        median_duration = sorted([d['duration_days'] for d in durations])[len(durations) // 2]
        on_time_percent = sum(1 for d in durations if not d['overdue']) / len(durations) * 100
    else:
        avg_duration = median_duration = on_time_percent = 0

    # Группировка по типу заявления
    by_type = {}
    for req_type, _ in VacationRequest.REQUEST_TYPES:
        type_requests = [d for d in durations if d['type'] == req_type]
        if type_requests:
            by_type[req_type] = {
                'count': len(type_requests),
                'avg_duration': sum(d['duration_days'] for d in type_requests) / len(type_requests),
                'on_time_percent': sum(1 for d in type_requests if not d['overdue']) / len(type_requests) * 100
            }

    context = {
        'total_requests': queryset.count(),
        'approved_count': approved_requests.count(),
        'avg_duration': round(avg_duration, 2),
        'median_duration': round(median_duration, 2),
        'on_time_percent': round(on_time_percent, 2),
        'durations': durations[:50],  # последние 50 для таблицы
        'by_type': by_type,
        'filters': {
            'period_start': period_start,
            'period_end': period_end,
            'type': request_type,
            'status': status,
        }
    }

    return render(request, 'vacations/report_duration.html', context)


def _calculate_sla(self, request):
    """Рассчитать общий SLA для заявки (сумма sla_days по всем шагам)"""
    routes = ApprovalRoute.objects.filter(type=request.request_type)
    return sum(route.sla_days for route in routes)


def export_csv(request):
    """Экспорт отчёта в CSV"""

    # Получаем заявки с фильтрами (как в отчёте)
    queryset = VacationRequest.objects.filter(status='approved', approved_at__isnull=False)

    # Применяем те же фильтры, что и в отчёте
    period_start = request.GET.get('period_start')
    period_end = request.GET.get('period_end')
    request_type = request.GET.get('type')

    if period_start:
        queryset = queryset.filter(created_at__date__gte=period_start)
    if period_end:
        queryset = queryset.filter(created_at__date__lte=period_end)
    if request_type:
        queryset = queryset.filter(request_type=request_type)

    # Создаём HTTP-ответ с CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="vacation_report_{timezone.now().date()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Тип', 'Сотрудник', 'Дата создания', 'Дата утверждения',
                     'Длительность (дней)', 'SLA (дней)', 'Просрочено'])

    for req in queryset:
        if req.approved_at and req.created_at:
            duration = (req.approved_at - req.created_at).total_seconds() / 86400
            sla = _calculate_sla_for_request(req)
            overdue = duration > sla

            writer.writerow([
                req.id,
                req.get_request_type_display(),
                req.employee.name,
                req.created_at.strftime('%d.%m.%Y %H:%M'),
                req.approved_at.strftime('%d.%m.%Y %H:%M'),
                round(duration, 2),
                sla,
                'Да' if overdue else 'Нет'
            ])

    return response


def export_json(request):
    """Экспорт отчёта в JSON"""

    # Получаем заявки с фильтрами
    queryset = VacationRequest.objects.filter(status='approved', approved_at__isnull=False)

    period_start = request.GET.get('period_start')
    period_end = request.GET.get('period_end')
    request_type = request.GET.get('type')

    if period_start:
        queryset = queryset.filter(created_at__date__gte=period_start)
    if period_end:
        queryset = queryset.filter(created_at__date__lte=period_end)
    if request_type:
        queryset = queryset.filter(request_type=request_type)

    # Формируем данные для JSON
    data = []
    for req in queryset:
        if req.approved_at and req.created_at:
            duration = (req.approved_at - req.created_at).total_seconds() / 86400
            sla = _calculate_sla_for_request(req)

            data.append({
                'id': req.id,
                'type': req.get_request_type_display(),
                'type_code': req.request_type,
                'employee': {
                    'id': req.employee.id,
                    'name': req.employee.name,
                    'position': req.employee.position
                },
                'created_at': req.created_at.isoformat(),
                'approved_at': req.approved_at.isoformat(),
                'duration_days': round(duration, 2),
                'sla_days': sla,
                'overdue': duration > sla
            })

    # Возвращаем JSON
    return JsonResponse({
        'generated_at': timezone.now().isoformat(),
        'filters': {
            'period_start': period_start,
            'period_end': period_end,
            'type': request_type,
        },
        'count': len(data),
        'results': data
    }, json_dumps_params={'ensure_ascii': False, 'indent': 2})


def calculate_sla_for_request(request_obj):
    """Рассчитать общий SLA для конкретной заявки"""
    routes = ApprovalRoute.objects.filter(type=request_obj.request_type)
    return sum(route.sla_days for route in routes)


def report_duration(request):
    """Отчёт по длительности согласования заявок"""

    # Базовый queryset
    queryset = VacationRequest.objects.all()

    # Фильтры (из ТЗ)
    period_start = request.GET.get('period_start')
    period_end = request.GET.get('period_end')
    request_type = request.GET.get('type')
    status = request.GET.get('status')

    if period_start:
        queryset = queryset.filter(created_at__date__gte=period_start)
    if period_end:
        queryset = queryset.filter(created_at__date__lte=period_end)
    if request_type:
        queryset = queryset.filter(request_type=request_type)
    if status:
        queryset = queryset.filter(status=status)

    # Расчёт длительности согласования (для утверждённых заявок)
    approved_requests = queryset.filter(status='approved', approved_at__isnull=False)

    durations = []
    for req in approved_requests:
        if req.approved_at and req.created_at:
            duration = (req.approved_at - req.created_at).total_seconds() / 86400  # в днях
            sla = calculate_sla_for_request(req)  # ИСПРАВЛЕНО: используем функцию, а не self
            durations.append({
                'id': req.id,
                'type': req.get_request_type_display(),
                'employee': req.employee.name,
                'created_at': req.created_at,
                'approved_at': req.approved_at,
                'duration_days': round(duration, 2),
                'sla_days': sla,
                'overdue': duration > sla
            })

    # Статистика
    if durations:
        avg_duration = sum(d['duration_days'] for d in durations) / len(durations)
        median_duration = sorted([d['duration_days'] for d in durations])[len(durations) // 2]
        on_time_percent = sum(1 for d in durations if not d['overdue']) / len(durations) * 100
    else:
        avg_duration = median_duration = on_time_percent = 0

    # Группировка по типу заявления
    by_type = {}
    for req_type, _ in VacationRequest.REQUEST_TYPES:
        type_requests = [d for d in durations if d['type'] == req_type]
        if type_requests:
            by_type[req_type] = {
                'count': len(type_requests),
                'avg_duration': sum(d['duration_days'] for d in type_requests) / len(type_requests),
                'on_time_percent': sum(1 for d in type_requests if not d['overdue']) / len(type_requests) * 100
            }

    context = {
        'total_requests': queryset.count(),
        'approved_count': approved_requests.count(),
        'avg_duration': round(avg_duration, 2),
        'median_duration': round(median_duration, 2),
        'on_time_percent': round(on_time_percent, 2),
        'durations': durations[:50],  # последние 50 для таблицы
        'by_type': by_type,
        'filters': {
            'period_start': period_start,
            'period_end': period_end,
            'type': request_type,
            'status': status,
        }
    }

    return render(request, 'vacations/report_duration.html', context)