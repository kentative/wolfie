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

def has_required_permissions():
    async def predicate(ctx):
        # Allow if user has 'manage_guild' permission
        if ctx.author.guild_permissions.manage_guild:
            return True

        # Allow if user has any of the specified roles (case-insensitive)
        if any(str(role.name).lower() in ALLOWED_ROLES for role in ctx.author.roles):
            return True

        return False

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

def parse_datetime(input_dt: str, now: datetime, tz: str='UTC'):

    # only use hour
    now = now.replace(minute=0, second=0, microsecond=0)

    try:
        dt = datetime.strptime(input_dt, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            dt = datetime.strptime(input_dt, "%m-%d %I%p")
            dt = now.replace(month=dt.month, day=dt.day, hour=dt.hour)
        except ValueError:
            try:
                dt = datetime.strptime(input_dt, "%H")
                dt = now.replace(hour=dt.hour)
            except ValueError:
                return None

    try:
        zone: tzinfo = pytz.timezone(tz)  # Validate timezone
    except pytz.UnknownTimeZoneError:
        logger.warn(f'Invalid timezone specified: {tz}, defaulting to UTC')
        zone = pytz.UTC
    return dt.astimezone(zone)
