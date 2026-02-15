from django.contrib import admin
from .models import VacationBalance, VacationRequest

@admin.register(VacationBalance)
class VacationBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'year', 'total_days', 'used_days', 'remaining_days']
    list_filter = ['year']

@admin.register(VacationRequest)
class VacationRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'start_date', 'end_date', 'status', 'days_count']
    list_filter = ['status', 'start_date']
    search_fields = ['employee__name']