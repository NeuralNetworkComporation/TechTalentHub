from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'position', 'hire_date', 'is_active']
    list_filter = ['is_active', 'position']
    search_fields = ['name', 'email']