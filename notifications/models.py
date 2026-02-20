from django.db import models
from django.contrib.auth.models import User
from core.models import TimeStampedModel

class Notification(TimeStampedModel):
    """Модель уведомлений"""
    
    TYPES = [
        ('info', 'Информация'),
        ('success', 'Успех'),
        ('warning', 'Предупреждение'),
        ('danger', 'Ошибка'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPES, default='info')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"