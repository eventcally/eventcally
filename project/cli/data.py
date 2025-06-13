import click
from flask.cli import AppGroup

from project import app
from project.init_data import create_initial_data

data_cli = AppGroup("data")


@data_cli.command("seed")
def seed():
    create_initial_data()
    click.echo("Seed done.")


app.cli.add_command(data_cli)
