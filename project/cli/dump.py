import click
from flask.cli import AppGroup

from project import app
from project.services import dump

dump_cli = AppGroup("dump")


@dump_cli.command("all")
def dump_all():
    dump.dump_all()


@dump_cli.command("organization")
@click.argument("admin_unit_id")
def dump_admin_unit(admin_unit_id):
    dump.dump_admin_unit(admin_unit_id)


app.cli.add_command(dump_cli)
