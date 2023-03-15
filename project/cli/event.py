from flask.cli import AppGroup

from project import app
from project.services import event

event_cli = AppGroup("event")


@event_cli.command("update-recurring-dates")
def update_recurring_dates():
    event.update_recurring_dates()


app.cli.add_command(event_cli)
