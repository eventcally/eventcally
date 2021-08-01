# pragma: no cover
import click
from flask.cli import AppGroup

from project import app, db
from project.init_data import create_initial_data

database_cli = AppGroup("database")


@database_cli.command("drop-all")
def drop_all():
    db.drop_all()
    click.echo("Done.")


@database_cli.command("create-all")
def create_all():
    db.create_all()
    click.echo("Done.")


@database_cli.command("seed")
def seed():
    create_initial_data()
    click.echo("Done.")


app.cli.add_command(database_cli)
