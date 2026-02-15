from django.db import models
from django.contrib.auth.models import User

class TimeStampedModel(models.Model):
    """Абстрактная модель с датами создания и обновления"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True