import logging
import os
from logging.handlers import RotatingFileHandler

DEFAULT_LOGGING_LEVEL = os.getenv("DEFAULT_LOGGING_LEVEL", "INFO")

def init_logger(logger_name:str):

    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger = logging.getLogger(logger_name)
    logger.setLevel(DEFAULT_LOGGING_LEVEL)

    # Create handlers
    console_handler = logging.StreamHandler()
    file_handler = RotatingFileHandler(
        'logs/wolfie.log',
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5,
        delay=True
    )

    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - Line: %(lineno)d - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
