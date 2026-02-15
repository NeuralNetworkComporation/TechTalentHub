from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from onboarding.views import api_stats
from analytics.views import dashboard as analytics_dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # API
    path('api/stats/', api_stats, name='api_stats'),

    # Основные разделы
    path('onboarding/', include('onboarding.urls')),
    path('employees/', include('users.urls')),
    path('vacations/', include('vacations.urls')),  # создадим позже
    path('analytics/', analytics_dashboard, name='analytics_dashboard'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)