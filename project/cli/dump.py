from flask.cli import AppGroup

from project import app
from project.services import dump

dump_cli = AppGroup("dump")


@dump_cli.command("all")
def dump_all():
    dump.dump_all()


app.cli.add_command(dump_cli)
