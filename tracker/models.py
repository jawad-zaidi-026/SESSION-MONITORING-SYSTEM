from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import localtime

class SessionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    computer_name = models.CharField(max_length=100, null=True, blank=True)
    login_time = models.DateTimeField()
    logout_time = models.DateTimeField(null=True, blank=True)
    session_duration = models.DurationField(null=True, blank=True)

    def is_anomalous(self):
        local_login = localtime(self.login_time)
        return local_login.hour < 7 or local_login.hour > 21

    is_anomalous.boolean = True
    is_anomalous.short_description = 'Anomalous?'

    def __str__(self):
        return f"{self.user.username} - {self.login_time.strftime('%Y-%m-%d %H:%M:%S')}"
