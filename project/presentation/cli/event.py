from flask.cli import AppGroup

from project.presentation.cli import click_logging

event_cli = AppGroup("event")


@event_cli.command("update-recurring-dates")
@click_logging
def update_recurring_dates():
    from project.celery_tasks import update_recurring_dates

    update_recurring_dates()
