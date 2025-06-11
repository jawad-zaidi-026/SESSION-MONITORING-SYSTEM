from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils.timezone import now
from .models import SessionLog

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    SessionLog.objects.create(user=user, login_time=now())

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    try:
        latest_session = SessionLog.objects.filter(user=user, logout_time__isnull=True).latest('login_time')
        latest_session.logout_time = now()
        latest_session.save()
    except SessionLog.DoesNotExist:
        pass
