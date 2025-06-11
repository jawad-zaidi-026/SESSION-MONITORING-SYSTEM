import os
import django
import datetime
import xml.etree.ElementTree as ET
import subprocess
from django.utils.timezone import make_aware

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sessionmonitor.settings")
django.setup()

from django.contrib.auth.models import User
from tracker.models import SessionLog

# Function to parse Windows Event Logs (Logon/Logoff events)
def extract_windows_logs():
    # Event IDs: 4624 = Logon, 4634 = Logoff
    logon_events = subprocess.check_output(
        'wevtutil qe Security "/q:*[System[(EventID=4624)]]" /f:xml /c:50', shell=True
    ).decode('utf-8')
    logoff_events = subprocess.check_output(
        'wevtutil qe Security "/q:*[System[(EventID=4634)]]" /f:xml /c:50', shell=True
    ).decode('utf-8')

    logon_entries = ET.fromstring(f"<Events>{logon_events}</Events>")
    logoff_entries = ET.fromstring(f"<Events>{logoff_events}</Events>")

    logs = {}

    for entry in logon_entries.findall("Event"):
        timestamp = entry.find("System/TimeCreated").attrib["SystemTime"]
        user_elem = entry.find(".//Data[@Name='TargetUserName']")
        if user_elem is None:
            continue
        username = user_elem.text
        time = make_aware(datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00")))
        logs.setdefault(username, []).append({"login": time, "logout": None})

    for entry in logoff_entries.findall("Event"):
        timestamp = entry.find("System/TimeCreated").attrib["SystemTime"]
        user_elem = entry.find(".//Data[@Name='TargetUserName']")
        if user_elem is None:
            continue
        username = user_elem.text
        time = make_aware(datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00")))
        if username in logs:
            for session in logs[username]:
                if session["logout"] is None:
                    session["logout"] = time
                    break

    # Save to DB
    for username, sessions in logs.items():
        user, _ = User.objects.get_or_create(username=username)
        for session in sessions:
            SessionLog.objects.get_or_create(
                user=user,
                login_time=session["login"],
                logout_time=session["logout"]
            )

if __name__ == "__main__":
    extract_windows_logs()
    print("Windows session logs extracted and saved.")

from django.core.mail import send_mail
from django.conf import settings
from tracker.models import SessionLog
from django.utils import timezone
from datetime import timedelta

from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from tracker.models import SessionLog

def analyze_and_send_report():
    today = timezone.now().date()
    start = timezone.make_aware(datetime.datetime.combine(today, datetime.time.min))
    end = timezone.make_aware(datetime.datetime.combine(today, datetime.time.max))

    logs = SessionLog.objects.filter(login_time__range=(start, end))

    if not logs.exists():
        print("No session logs found for today.")
        return

    report = "🖥️ Daily Session Log Report:\n\n"
    anomalies = "\n🚨 Anomalies Detected:\n"
    anomaly_found = False

    user_sessions = {}

    for log in logs:
        duration = (log.logout_time - log.login_time) if log.logout_time else timedelta(0)
        user_sessions.setdefault(log.user.username, []).append(duration)

        # === Anomaly Detection ===
        login_hour = log.login_time.hour
        is_weekend = log.login_time.weekday() >= 5  # Saturday = 5, Sunday = 6
        is_odd_hour = login_hour < 6 or login_hour > 22
        is_long_session = duration > timedelta(hours=10)

        if is_odd_hour or is_weekend or is_long_session:
            anomaly_found = True
            anomalies += f"🔸 {log.user.username} logged in at {log.login_time.strftime('%H:%M')} on {log.login_time.strftime('%A')}\n"
            if is_odd_hour:
                anomalies += "   ↳ ❗ Odd hour login\n"
            if is_weekend:
                anomalies += "   ↳ ❗ Weekend login\n"
            if is_long_session:
                anomalies += f"   ↳ ❗ Long session: {duration}\n"

    # === Add regular session summary ===
    for username, durations in user_sessions.items():
        total_time = sum(durations, timedelta())
        report += f"👤 {username}: {str(total_time)} total time\n"

    if anomaly_found:
        report += anomalies

    # Send email
    send_mail(
        subject='Daily Session Log Report',
        message=report,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['jawadzaidi026@gmail.com'],
    )

    print("✅ Real report: session analysis complete and email sent.")
