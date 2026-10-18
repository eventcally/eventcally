import logging
from functools import wraps

from flask import Flask, current_app


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


def init_cli(app: Flask):
    """Register the Flask CLI command groups with the Flask app instance."""
    from project.presentation.cli.cache import cache_cli
    from project.presentation.cli.data import data_cli
    from project.presentation.cli.dump import dump_cli
    from project.presentation.cli.event import event_cli
    from project.presentation.cli.seo import seo_cli
    from project.presentation.cli.user import user_cli

    app.cli.add_command(cache_cli)
    app.cli.add_command(data_cli)
    app.cli.add_command(dump_cli)
    app.cli.add_command(event_cli)
    app.cli.add_command(seo_cli)
    app.cli.add_command(user_cli)

    if app.config.get("ENABLE_TEST_CLI"):  # pragma: no cover
        from project.presentation.cli.test import test_cli

        app.cli.add_command(test_cli)
