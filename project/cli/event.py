import click
from flask.cli import AppGroup

from project import app
from project.cli import click_logging
from project.services import event

event_cli = AppGroup("event")


@event_cli.command("update-recurring-dates")
@click_logging
def update_recurring_dates():
    event.update_recurring_dates()


@event_cli.command("create-bulk-references")
@click.argument("admin_unit_id")
@click.argument("postal_codes", nargs=-1)
@click_logging
def create_bulk_event_references(admin_unit_id, postal_codes):
    event.create_bulk_event_references(admin_unit_id, list(postal_codes))


app.cli.add_command(event_cli)
