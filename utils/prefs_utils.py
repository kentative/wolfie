
def get_timezone(user_prefs: dict):
    return user_prefs.get("timezone", 'UTC')

def get_alias(user_prefs: dict):
    return user_prefs.get("alias", user_prefs.get("name", user_prefs.get("id", None)))

def get_alias_by_id(user_id: str, all_prefs: dict):
    prefs = all_prefs.get(str(user_id), {})
    return get_alias(prefs)

def get_timezone_by_id(user_id: str, all_prefs: dict):
    prefs = all_prefs.get(str(user_id), {})
    return get_timezone(prefs)
