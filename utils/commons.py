import json

from utils.logger import init_logger

USER_PREFERENCES_PATH = "data/user_preferences.json"

logger = init_logger('utils')

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