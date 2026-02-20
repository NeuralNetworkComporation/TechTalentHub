from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Employee

@login_required
def employee_list(request):
    """Список всех сотрудников"""
    employees = Employee.objects.filter(is_active=True).order_by('name')
    return render(request, 'employees/list.html', {
        'employees': employees
    })

@login_required
def employee_detail(request, pk):
    """Детальная страница сотрудника"""
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'employees/detail.html', {
        'employee': employee
    })