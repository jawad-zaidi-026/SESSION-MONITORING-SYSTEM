import os
import django
import random
from datetime import datetime, timedelta
import pytz

# ⚙️ Set up Django environment before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sessionmonitor.settings")
django.setup()

from django.contrib.auth.models import User
from django.utils.timezone import now
from tracker.models import SessionLog

# 🌍 Define India timezone
india_tz = pytz.timezone("Asia/Kolkata")
current_time = now().astimezone(india_tz)

# 👥 Create or get users
usernames = ['jawad', 'admin', 'alex', 'sara']
users = {uname: User.objects.get_or_create(username=uname)[0] for uname in usernames}

# 📅 Generate logs
for uname in usernames:
    user = users[uname]
    for i in range(7):  # Past 7 days
        base_day = (current_time - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)

        is_anomaly = random.choice([True, False])
        if is_anomaly:
            anomaly_type = random.choice(['early_login', 'late_login', 'short_session', 'long_session'])

            if anomaly_type == 'early_login':
                login_time = base_day.replace(hour=random.randint(3, 6), minute=random.randint(0, 59))
                logout_time = login_time + timedelta(hours=2)

            elif anomaly_type == 'late_login':
                login_time = base_day.replace(hour=random.randint(21, 23), minute=random.randint(0, 59))
                logout_time = login_time + timedelta(hours=2)

            elif anomaly_type == 'short_session':
                login_time = base_day.replace(hour=9, minute=30)
                logout_time = login_time + timedelta(seconds=random.randint(10, 50))

            elif anomaly_type == 'long_session':
                login_time = base_day.replace(hour=8, minute=0)
                logout_time = login_time + timedelta(hours=random.randint(9, 12))

        else:
            login_hour = random.randint(7, 20)
            login_minute = random.randint(0, 59)
            login_time = base_day.replace(hour=login_hour, minute=login_minute)
            logout_time = login_time + timedelta(hours=random.randint(1, 5))

        # 🕒 Timezone-aware timestamps
        if login_time.tzinfo is None:
            login_time = india_tz.localize(login_time)
        else:
            login_time = login_time.astimezone(india_tz)

        if logout_time.tzinfo is None:
            logout_time = india_tz.localize(logout_time)
        else:
            logout_time = logout_time.astimezone(india_tz)

        # ⛔ Prevent logout_time in future or before login_time
        if logout_time > current_time:
            logout_time = min(current_time, login_time + timedelta(minutes=15))

        if logout_time < login_time:
            logout_time = login_time + timedelta(minutes=5)

        # ⏳ Calculate session duration
        session_duration = logout_time - login_time

        # 📥 Save the session log
        SessionLog.objects.create(
            user=user,
            login_time=login_time,
            logout_time=logout_time,
            session_duration=session_duration
        )

        print(f"📄 {user.username} | Login: {login_time.strftime('%Y-%m-%d %H:%M')} | Logout: {logout_time.strftime('%Y-%m-%d %H:%M')}")
        
print("✅ Successfully populated session logs with corrected timestamps in Asia/Kolkata.")