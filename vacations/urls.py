from django.urls import path
from . import views

app_name = 'vacations'

urlpatterns = [
    path('', views.vacation_list, name='list'),
    path('create/', views.vacation_create, name='create'),
    path('<int:pk>/', views.vacation_detail, name='detail'),
    path('calendar/', views.vacation_calendar, name='calendar'),
    path('<int:pk>/approve/', views.vacation_approve, name='approve'),
    path('<int:pk>/reject/', views.vacation_reject, name='reject'),
    path('api/calendar/', views.calendar_api, name='calendar_api'),
]