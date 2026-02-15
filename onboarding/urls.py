from django.urls import path
from . import views

app_name = 'onboarding'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('employee/<int:employee_id>/', views.employee_checklist, name='employee_checklist'),
    path('api/toggle-task/<int:task_id>/', views.toggle_task, name='toggle_task'),
]