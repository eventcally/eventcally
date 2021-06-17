import click
from flask.cli import AppGroup, with_appcontext

from project import app, db
from project.dateutils import berlin_tz
from project.services.event import (
    get_recurring_events,
    update_event_dates_with_recurrence_rule,
)

event_cli = AppGroup("event")


@event_cli.command("update-recurring-dates")
@with_appcontext
def update_recurring_dates():
    db.session.execute("SET timezone TO :val;", {"val": berlin_tz.zone})
    events = get_recurring_events()

    for event in events:
        if event.recurrence_rule:
            update_event_dates_with_recurrence_rule(event)
            db.session.commit()

    click.echo(f"{len(events)} event(s) were updated.")


app.cli.add_command(event_cli)
