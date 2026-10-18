import logging
from functools import wraps

from flask import current_app


def click_logging(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = current_app.logger
        original_level = logger.level
        logger.setLevel(logging.INFO)
        result = func(*args, **kwargs)
        logger.setLevel(original_level)
        return result

    return wrapper
