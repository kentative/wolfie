from utils.commons import load_user_prefs

# load this list for all cogs
user_prefs : dict = load_user_prefs()

def get_timezone(ctx):
    return (user_prefs.get(str(ctx.author.id), {})
            .get('timezone', 'UTC'))

def get_alias(ctx):
    return (user_prefs.get(str(ctx.author.id), {})
            .get('alias', ctx.author.name))

def get_alias_by_id(user_id:str, default:str):
    return user_prefs.get(str(user_id), {}).get('alias', default)


def get_pref(user_id:str):
    return user_prefs.get(str(user_id), {})
