import os
import django
import random
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.contrib.auth.models import User
from tracker.models import SessionLog
import pytz  # Correct timezone handling

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sessionmonitor.settings")
django.setup()

# Define India timezone
india_tz = pytz.timezone("Asia/Kolkata")

# Create or get users
usernames = ['jawad', 'admin', 'alex', 'sara']
users = {uname: User.objects.get_or_create(username=uname)[0] for uname in usernames}

# Generate logs
for uname in usernames:
    user = users[uname]
    for i in range(7):  # Generate logs for past 7 days
        base_day = now() - timedelta(days=i)  # Always store past timestamps
        
        # Convert base_day to naive datetime before applying timezone
        base_day = base_day.replace(tzinfo=None)

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
            # Normal session between 7 AM and 9 PM
            login_hour = random.randint(7, 20)
            login_minute = random.randint(0, 59)
            login_time = base_day.replace(hour=login_hour, minute=login_minute)
            logout_time = login_time + timedelta(hours=random.randint(1, 5))

        # Apply timezone correctly before saving
        login_time = india_tz.localize(login_time)
        logout_time = india_tz.localize(logout_time)

        SessionLog.objects.create(
            user=user,
            login_time=login_time,
            logout_time=logout_time
        )

print("✅ Successfully populated session logs with corrected timestamps in Asia/Kolkata.")