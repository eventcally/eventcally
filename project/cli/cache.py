from flask.cli import AppGroup

from project import app
from project.cli import click_logging
from project.services import cache

cache_cli = AppGroup("cache")


@cache_cli.command("clear-images")
@click_logging
def clear_images():
    cache.clear_images()


app.cli.add_command(cache_cli)
