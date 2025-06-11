import os
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sessionmonitor.settings")
django.setup()

from tracker.views import send_email

# Call the function (None since it's not a web request)
send_email(None)
