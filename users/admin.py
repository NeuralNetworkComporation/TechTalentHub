from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'position', 'hire_date', 'is_active']
    list_filter = ['is_active', 'position']
    search_fields = ['name', 'email']

    # Добавляем поле manager в форму редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'bitrix_id', 'name', 'email', 'position')
        }),
        ('Руководство', {
            'fields': ('manager',),
            'description': 'Укажите руководителя для этого сотрудника'
        }),
        ('Даты и статус', {
            'fields': ('hire_date', 'is_active')
        }),
    )

    # Делаем поле manager более удобным для выбора
    raw_id_fields = ['manager']
    autocomplete_lookup_fields = {
        'fk': ['manager'],
    }