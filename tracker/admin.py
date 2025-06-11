from django.contrib import admin
from .models import SessionLog

@admin.register(SessionLog)
class SessionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'logout_time', 'is_anomalous')
    list_filter = ('user',)
    ordering = ('login_time',)
