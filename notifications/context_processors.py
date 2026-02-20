from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {
            'notifications_count': count,
            'notifications': Notification.objects.filter(user=request.user)[:5]
        }
    return {}