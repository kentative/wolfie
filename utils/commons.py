import json

from utils.logger import init_logger

logger = init_logger('utils')

def save_data(data:dict[str, str], path:str):
    with open(path, "w") as file:
        json.dump(data, file, indent=4)


def load_data(path:str):
    try:
        with open(path, "r") as file:
            data = json.load(file)
            return data
    except Exception as e:
        logger.info(f'{e}. Creating default name list')
        return {}