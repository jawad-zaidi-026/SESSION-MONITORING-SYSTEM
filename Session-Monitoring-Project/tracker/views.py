from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib import messages
from django.utils.timezone import now, make_aware, localtime
from django.conf import settings
from datetime import datetime, timedelta
import pytz
from .models import SessionLog

# 🔍 Anomaly logic
def is_anomalous(log):
    notes = []

    if log.logout_time:
        if log.logout_time < log.login_time:
            notes.append("⚠️ Logout before login")
        elif log.logout_time > now().astimezone(pytz.timezone("Asia/Kolkata")):
            notes.append("⚠️ Future logout time")

    duration = (log.logout_time - log.login_time) if log.logout_time else timedelta(0)
    if duration > timedelta(hours=8):
        notes.append("⚠️ Excessive session (>8h)")

    return notes if notes else ["✓ Normal"]

# 🏠 Home View with Pagination and Status
def home(request):
    all_logs = SessionLog.objects.select_related('user').order_by('-login_time')
    paginator = Paginator(all_logs, 10)
    page_number = request.GET.get('page')
    page_logs = paginator.get_page(page_number)

    for log in page_logs:
        log.login_time = localtime(log.login_time)
        log.logout_time = localtime(log.logout_time) if log.logout_time else None

        if log.logout_time:
            if log.logout_time <= now():
                delta = log.logout_time - log.login_time
                hours, remainder = divmod(delta.total_seconds(), 3600)
                minutes = remainder // 60
                log.duration_str = f"{int(hours)}h {int(minutes)}m" if hours else f"{int(minutes)}m"
                log.logout_status = log.logout_time.strftime('%I:%M %p, %b %d')
            else:
                log.duration_str = "Invalid (future logout)"
                log.logout_status = "Invalid"
        else:
            log.duration_str = "Active"
            log.logout_status = "Active"

        log.anomalies = is_anomalous(log)

    active_users = SessionLog.objects.filter(logout_time__isnull=True).count()

    return render(request, 'home.html', {
        'logs': page_logs,
        'active_users': active_users
    })

# 📧 Send Daily Email Report
def send_email(request=None):
    today = now().date()
    start = make_aware(datetime.combine(today, datetime.min.time()))
    end = make_aware(datetime.combine(today, datetime.max.time()))

    logs = SessionLog.objects.filter(login_time__range=(start, end))
    if not logs.exists():
        if request:
            messages.warning(request, "⚠️ No session logs found for today.")
            return HttpResponseRedirect(reverse("home"))
        else:
            print("⚠️ No session logs found for today.")
            return

    report = "🖥️ *Daily Session Log Report*:\n\n"
    user_sessions = {}

    for log in logs:
        log.login_time = localtime(log.login_time)
        log.logout_time = localtime(log.logout_time) if log.logout_time else None

        username = log.user.username
        user_sessions.setdefault(username, {"entries": [], "total_duration": timedelta(), "anomalies": []})

        duration = (log.logout_time - log.login_time) if log.logout_time else timedelta(0)
        anomaly_notes = is_anomalous(log)

        icon = "🕓" if log.logout_time else "🟢"
        entry = f"{icon} {log.login_time.strftime('%H:%M')} to " \
                f"{log.logout_time.strftime('%H:%M') if log.logout_time else 'Active'} ({str(duration).split('.')[0]})"

        if anomaly_notes:
            entry += f" ⚠️ {' | '.join(anomaly_notes)}"
            user_sessions[username]["anomalies"].extend(anomaly_notes)

        user_sessions[username]["entries"].append(entry)
        user_sessions[username]["total_duration"] += duration

    for username, data in user_sessions.items():
        entries = data["entries"]
        total = str(data["total_duration"]).split('.')[0]

        report += f"\n👤 {username}:\n\n" + "\n".join(entries)
        report += f"\n🧮 Total Time: {total}"

        if data["anomalies"]:
            unique_anomalies = set(data["anomalies"])
            report += f"\n🚨 Anomalies: {' | '.join(unique_anomalies)}"

        report += "\n" + ("-" * 40) + "\n"

    try:
        send_mail(
            subject='📊 Daily Session Log Report',
            message=report,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['jawadzaidi026@gmail.com'],
            fail_silently=False,
        )
        if request:
            messages.success(request, "✅ Email sent successfully!")
            return HttpResponseRedirect(reverse("home"))
        else:
            print("✅ Email sent.")
    except Exception as e:
        if request:
            return HttpResponse(f"❌ Failed to send email: {str(e)}")
        else:
            print(f"❌ Email failed: {str(e)}")

# 📊 Dashboard (with filters and graphs)
def dashboard(request):
    user = request.GET.get('user')
    start = request.GET.get('start')
    end = request.GET.get('end')

    logs = SessionLog.objects.all()

    if user:
        logs = logs.filter(user__username__icontains=user)
    if start:
        start = localtime(datetime.strptime(start, "%Y-%m-%d"))
        logs = logs.filter(login_time__date__gte=start)
    if end:
        end = localtime(datetime.strptime(end, "%Y-%m-%d"))
        logs = logs.filter(logout_time__date__lte=end)

    user_data = {}
    anomaly_count = 0

    # Convert timestamps before display
    for log in logs:
        log.login_time = localtime(log.login_time)
        log.logout_time = localtime(log.logout_time) if log.logout_time else None

        username = log.user.username
        duration = (log.logout_time - log.login_time).total_seconds() / 3600 if log.logout_time else 0
        user_data[username] = user_data.get(username, 0) + duration

        if is_anomalous(log) != ["✓ Normal"]:
            anomaly_count += 1

    context = {
        'logs': logs,
        'usernames': list(user_data.keys()),
        'durations': [round(v, 2) for v in user_data.values()],
        'anomaly_count': anomaly_count
    }

    return render(request, 'dashboard.html', context)

# 🚨 View Only Anomalies
def anomalies_view(request):
    logs = SessionLog.objects.all()
    anomalies = []

    for log in logs:
        log.login_time = localtime(log.login_time)
        log.logout_time = localtime(log.logout_time) if log.logout_time else None

        notes = is_anomalous(log)
        if notes != ["✓ Normal"]:
            log.anomalies = notes
            anomalies.append(log)

    return render(request, 'anomalies.html', {'anomalies': anomalies})

import json

def dashboard_view(request):
    usernames = ['Alice', 'Bob']
    durations = [5, 7]
    return render(request, 'dashboard.html', {
        'usernames': json.dumps(usernames),
        'durations': json.dumps(durations)
    })