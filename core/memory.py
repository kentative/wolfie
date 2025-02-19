from utils.commons import load_user_prefs, save_user_prefs
from utils.logger import init_logger

logger = init_logger('Memory')

# load this list for all cogs
USER_PREFS : dict = load_user_prefs()

def get_timezone(ctx):
    return (USER_PREFS.get(str(ctx.author.id), {})
            .get('timezone', 'UTC'))

def get_timezone_by_id(user_id:str):
    return (USER_PREFS.get(str(user_id), {})
            .get('timezone', 'UTC'))

def get_alias(ctx):
    return (USER_PREFS.get(str(ctx.author.id), {})
            .get('alias', ctx.author.name))

def get_alias_by_id(user_id:str, default:str):
    return USER_PREFS.get(str(user_id), {}).get('alias', default)

def has_prefs(user_id:str):
    return user_id in USER_PREFS

def get_prefs(user_id:str):
    prefs = USER_PREFS.get(str(user_id), {})
    if not prefs:
        prefs = create_default_preferences

    return prefs

def create_default_preferences(ctx):
    prefs = {
        'name': ctx.author.display_name,
        'alias': ctx.author.display_name,
        'timezone': 'UTC'
    }
    USER_PREFS[str(ctx.author.id)] = prefs
    logger.info(f'created default preferences for {ctx.author.id} = {prefs}')
    save_user_prefs(USER_PREFS)
