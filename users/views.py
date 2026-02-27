from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Employee
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

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


def role_selection(request):
    """Страница выбора роли для входа"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, 'Неверный логин или пароль')

    # Список тестовых пользователей для демо
    demo_users = [
        {'username': 'ivanov', 'name': 'Иван Иванов', 'role': 'Сотрудник', 'password': 'ivanov123'},
        {'username': 'petrov', 'name': 'Петр Петров', 'role': 'Руководитель', 'password': 'petrov123'},
        {'username': 'anna', 'name': 'Анна Сидорова', 'role': 'HR-специалист', 'password': 'anna123'},
        {'username': 'admin', 'name': 'Администратор', 'role': 'Админ', 'password': 'admin123'},
    ]

    return render(request, 'users/role_selection.html', {'demo_users': demo_users})