import json
import os
from datetime import datetime, tzinfo

import pytz
from discord.ext import commands

from utils.logger import init_logger

WOLFIE_ADMIN_ROLE = os.getenv('WOLFIE_ADMIN_ROLE', 'leadership')
ALLOWED_ROLES = [ WOLFIE_ADMIN_ROLE.lower() ]
USER_PREFERENCES_PATH = "data/user_preferences.json"

logger = init_logger('utils')

MONTH_DAY_PATTERNS = [
    "%d/%m",     # 14/2
    "%m/%d",     # 2/14
    "%m-%d",     # 2-14
    "%d-%m",     # 14-2
]

DATE_PATTERNS = [
    "%Y-%m-%d",  # 2025-02-16
    "%d-%m-%Y",  # 16-02-2025
    "%m/%d/%Y",  # 02/16/2025
    "%d %b %Y",  # 16 Feb 2025
    "%d %B %Y"   # 16 February 2025
]

TIME_PATTERNS = [
    "%I%p",
    "%I:%M%p",
    "%H:%M",
    "%H",
    "%H:%M:%S",
    "%I:%M:%S%p"
]

def has_required_permissions():
    async def predicate(ctx):
        # Allow if user has 'manage_guild' permission
        if ctx.author.guild_permissions.manage_guild:
            return True

        # Allow if user has any of the specified roles (case-insensitive)
        if any(str(role.name).lower() in ALLOWED_ROLES for role in ctx.author.roles):
            return True

        # for testing
        return True

    return commands.check(predicate)


def save_user_prefs(data:dict[str, str]):
    with open(USER_PREFERENCES_PATH, "w") as file:
        json.dump(data, file, indent=4)


def load_user_prefs():
    try:
        with open(USER_PREFERENCES_PATH, "r") as file:
            data = json.load(file)
            return data
    except Exception as e:
        logger.info(f'{e}. Creating default preference file')
        return {}

def parse_date_input(input_date: str, user_tz: str='UTC'):
    """Attempts to parse the input date, if not parsable, return value based on now"""

    try:
        zone: tzinfo = pytz.timezone(user_tz)  # Validate timezone
    except pytz.UnknownTimeZoneError:
        logger.warn(f'Invalid timezone specified: {user_tz}, defaulting to UTC')
        zone = pytz.UTC

    # only use year, month and day
    now = datetime.now(zone)
    now = now.replace(hour=0, minute=0, second=0, microsecond=0)

    for pattern in DATE_PATTERNS:
        try:
            dt = datetime.strptime(input_date, pattern)
            dt = now.replace(month=dt.month, day=dt.day, year=dt.year)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # use current year
    for pattern in MONTH_DAY_PATTERNS:
        try:
            dt = datetime.strptime(input_date, pattern)
            dt = now.replace(month=dt.month, day=dt.day)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    logger.info(f"provided date input does not match patterns {input_date}")
    return None


def parse_time_input(input_time: str, user_tz: str='UTC'):
    """Attempts to parse the input date, if not parsable, return None"""

    try:
        zone: tzinfo = pytz.timezone(user_tz)  # Validate timezone
    except pytz.UnknownTimeZoneError:
        logger.warn(f'Invalid timezone specified: {user_tz}, defaulting to UTC')
        zone = pytz.UTC

    # only use hour
    now = datetime.now(zone)
    now = now.replace(minute=0, second=0, microsecond=0)

    for pattern in TIME_PATTERNS:
        try:
            dt = datetime.strptime(input_time, pattern)
            dt = now.replace(hour=dt.hour)
            return dt.strftime("%H:%M:%S")
        except ValueError:
            continue

    logger.info(f"provided time input does not match patterns {input_time}")
    return None


def parse_datetime(input_dt: str, user_tz: str='UTC'):
    """Attempts to parse the input datetime, if not parsable, return None"""

    try:
        zone: tzinfo = pytz.timezone(user_tz)  # Validate timezone
    except pytz.UnknownTimeZoneError:
        logger.warn(f'Invalid timezone specified: {user_tz}, defaulting to UTC')
        zone = pytz.UTC

    # only use hour
    now = datetime.now(zone)
    now = now.replace(minute=0, second=0, microsecond=0)

    try:
        dt = datetime.strptime(input_dt, "%Y-%m-%dT%H:%M:%S%z")
        dt = now.replace(month=dt.month, day=dt.day, hour=dt.hour)
    except ValueError:
        try:
            dt = datetime.strptime(input_dt, "%Y-%m-%d %H:%M:%S")
            dt = now.replace(month=dt.month, day=dt.day, hour=dt.hour)
        except ValueError:
            try:
                dt = datetime.strptime(input_dt, "%m-%d %I%p")
                dt = now.replace(month=dt.month, day=dt.day, hour=dt.hour)
            except ValueError:
                try:
                    dt = datetime.strptime(input_dt, "%I%p").time()
                    dt = now.replace(hour=dt.hour)
                except ValueError:
                    try:
                        dt = datetime.strptime(input_dt, "%H")
                        dt = now.replace(hour=dt.hour)
                    except ValueError:
                        return None
    return dt
