from datetime import datetime, timedelta

import pytz

DATE_DISPLAY_FORMAT = '%m-%d %H:%M %Z'
time_mapping = {"t1": "01:00 UTC", "t2": "11:00 UTC", "t3": "19:00 UTC"}

def get_weekend_dates(user_tz):
    """Returns the dates for the upcoming Saturday (d1) and Sunday (d2) in the user's local timezone."""
    today = datetime.now(pytz.UTC)
    saturday = today + timedelta(days=(5 - today.weekday()) % 7)
    sunday = saturday + timedelta(days=1)

    user_timezone = pytz.timezone(user_tz)
    saturday_local = saturday.astimezone(user_timezone)
    sunday_local = sunday.astimezone(user_timezone)
    return saturday_local.strftime('%m-%d'), sunday_local.strftime('%m-%d')

def convert_utc_to_local(user_tz: str, utc_date_time: str) -> datetime:
    """Converts a UTC time string (HH:MM UTC) to the user's local timezone."""
    user_timezone = pytz.timezone(user_tz)
    current_year = datetime.now().year
    utc_dt = datetime.strptime(
        f'{current_year}-{utc_date_time}',
        "%Y-%m-%d %H:%M UTC").replace(tzinfo=pytz.UTC)

    return utc_dt.astimezone(user_timezone)

def convert_timeslot_to_utc(day_slot: str, time_slot: str) -> str:
    """Returns "%m-%d %H:%M UTC" from a d1, t1 and timezone"""
    d1_date, d2_date = get_weekend_dates('UTC')
    date_mapping = {"d1": d1_date, "d2": d2_date}
    return f'{date_mapping.get(day_slot)} {time_mapping.get(time_slot)}'