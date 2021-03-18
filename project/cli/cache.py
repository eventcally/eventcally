import click
from flask.cli import AppGroup

from project import app, img_path
from project.utils import clear_files_in_dir

cache_cli = AppGroup("cache")


@cache_cli.command("clear-images")
def clear_images():
    click.echo("Clearing images..")
    clear_files_in_dir(img_path)
    click.echo("Done.")


app.cli.add_command(cache_cli)
