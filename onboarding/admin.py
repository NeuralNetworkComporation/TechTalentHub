from django.contrib import admin
from .models import OnboardingTask, EmployeeOnboarding

@admin.register(OnboardingTask)
class OnboardingTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'order']
    list_editable = ['order']

@admin.register(EmployeeOnboarding)
class EmployeeOnboardingAdmin(admin.ModelAdmin):
    list_display = ['employee', 'task', 'is_completed']
    list_filter = ['is_completed']