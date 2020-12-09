import click
from flask.cli import AppGroup
from project import app, db
from project.services.event import (
    get_recurring_events,
    update_event_dates_with_recurrence_rule,
)

event_cli = AppGroup("event")


@event_cli.command("update-recurring-dates")
def update_recurring_dates():
    events = get_recurring_events()

    for event in events:
        update_event_dates_with_recurrence_rule(event)
        db.session.commit()

    click.echo(f"{len(events)} event(s) where updated.")


app.cli.add_command(event_cli)
