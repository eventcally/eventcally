import json

import click
from flask.cli import AppGroup
from flask_security.confirmable import confirm_user
from sqlalchemy import MetaData

from project import app, db
from project.init_data import create_initial_data
from project.models import (
    AdminUnit,
    Event,
    EventAttendanceMode,
    EventReferenceRequest,
    EventReferenceRequestReviewStatus,
    EventSuggestion,
    Location,
)
from project.services.admin_unit import get_admin_unit_by_id, insert_admin_unit_for_user
from project.services.event import insert_event, upsert_event_category
from project.services.event_suggestion import insert_event_suggestion
from project.services.organizer import get_event_organizer
from project.services.place import get_event_places
from project.services.user import create_user, find_user_by_email, get_user

test_cli = AppGroup("test")


def _get_now_by_minute():
    from datetime import datetime

    from project.dateutils import get_now

    now = get_now()
    return datetime(
        now.year, now.month, now.day, now.hour, now.minute, tzinfo=now.tzinfo
    )


def _get_default_event_place_id(admin_unit_id):
    return get_event_places(admin_unit_id, limit=1)[0].id


def _get_default_organizer_id(admin_unit_id):
    admin_unit = get_admin_unit_by_id(admin_unit_id)
    return get_event_organizer(admin_unit_id, admin_unit.name).id


def _create_user(
    email="test@test.de", password="MeinPasswortIstDasBeste", confirm=True
):
    user = create_user(email, password)

    if confirm:
        confirm_user(user)

    db.session.commit()
    return user.id


@test_cli.command("reset")
@click.option("--seed/--no-seed", default=False)
def reset(seed):
    meta = MetaData(bind=db.engine, reflect=True)
    con = db.engine.connect()
    trans = con.begin()

    for table in meta.sorted_tables:
        con.execute(f'ALTER TABLE "{table.name}" DISABLE TRIGGER ALL;')
        con.execute(table.delete())
        con.execute(f'ALTER TABLE "{table.name}" ENABLE TRIGGER ALL;')

    trans.commit()

    if seed:
        create_initial_data()

    click.echo("Reset done.")


@test_cli.command("drop-all")
def drop_all():
    db.drop_all()
    click.echo("Drop all done.")


@test_cli.command("create-all")
def create_all():
    db.create_all()
    click.echo("Create all done.")


@test_cli.command("seed")
def seed():
    create_initial_data()
    click.echo("Seed done.")


def _create_admin_unit(user_id, name):
    user = get_user(user_id)

    admin_unit = AdminUnit()
    admin_unit.name = name
    admin_unit.short_name = name.lower().replace(" ", "")
    admin_unit.incoming_reference_requests_allowed = True
    admin_unit.location = Location()
    admin_unit.location.postalCode = "38640"
    admin_unit.location.city = "Goslar"
    insert_admin_unit_for_user(admin_unit, user)
    db.session.commit()

    return admin_unit.id


@test_cli.command("admin-unit-create")
@click.argument("user_email")
@click.argument("name", default="Meine Crew")
def create_admin_unit(user_email, name):
    user = find_user_by_email(user_email)
    admin_unit_id = _create_admin_unit(user.id, name)
    result = {"admin_unit_id": admin_unit_id}
    click.echo(json.dumps(result))


def _create_event(admin_unit_id):
    event = Event()
    event.admin_unit_id = admin_unit_id
    event.categories = [upsert_event_category("Other")]
    event.name = "Name"
    event.description = "Beschreibung"
    event.start = _get_now_by_minute()
    event.event_place_id = _get_default_event_place_id(admin_unit_id)
    event.organizer_id = _get_default_organizer_id(admin_unit_id)
    event.ticket_link = ""
    event.tags = ""
    event.price_info = ""
    event.attendance_mode = EventAttendanceMode.offline
    insert_event(event)
    db.session.commit()

    return event.id


@test_cli.command("event-create")
@click.argument("admin_unit_id")
def create_event(admin_unit_id):
    event_id = _create_event(admin_unit_id)
    result = {"event_id": event_id}
    click.echo(json.dumps(result))


def _create_reference_request(event_id, admin_unit_id):
    reference_request = EventReferenceRequest()
    reference_request.event_id = event_id
    reference_request.admin_unit_id = admin_unit_id
    reference_request.review_status = EventReferenceRequestReviewStatus.inbox
    db.session.add(reference_request)
    db.session.commit()
    return reference_request.id


@test_cli.command("reference-request-create")
@click.argument("event_id")
@click.argument("admin_unit_id")
def create_reference_request(event_id, admin_unit_id):
    reference_request_id = _create_reference_request(event_id, admin_unit_id)
    result = {"reference_request_id": reference_request_id}
    click.echo(json.dumps(result))


def _create_incoming_reference_request(admin_unit_id):
    other_user_id = _create_user("other@test.de")
    other_admin_unit_id = _create_admin_unit(other_user_id, "Other Crew")
    event_id = _create_event(other_admin_unit_id)
    reference_request_id = _create_reference_request(event_id, admin_unit_id)
    return (other_user_id, other_admin_unit_id, event_id, reference_request_id)


@test_cli.command("reference-request-create-incoming")
@click.argument("admin_unit_id")
def create_incoming_reference_request(admin_unit_id):
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = _create_incoming_reference_request(admin_unit_id)
    result = {
        "other_user_id": other_user_id,
        "other_admin_unit_id": other_admin_unit_id,
        "event_id": event_id,
        "reference_request_id": reference_request_id,
    }
    click.echo(json.dumps(result))


def _create_event_suggestion(admin_unit_id, free_text=False):
    suggestion = EventSuggestion()
    suggestion.admin_unit_id = admin_unit_id
    suggestion.contact_name = "Vorname Nachname"
    suggestion.contact_email = "vorname@nachname.de"
    suggestion.contact_email_notice = False
    suggestion.name = "Vorschlag"
    suggestion.description = "Beschreibung"
    suggestion.start = _get_now_by_minute()
    suggestion.categories = [upsert_event_category("Other")]

    if free_text:
        suggestion.event_place_text = "Freitext Ort"
        suggestion.organizer_text = "Freitext Organisator"
    else:
        suggestion.event_place_id = _get_default_event_place_id(admin_unit_id)
        suggestion.organizer_id = _get_default_organizer_id(admin_unit_id)

    insert_event_suggestion(suggestion)
    db.session.commit()
    return suggestion.id


@test_cli.command("suggestion-create")
@click.argument("admin_unit_id")
@click.option("--freetext/--no-freetext", default=False)
def create_event_suggestion(admin_unit_id, freetext):
    event_suggestion_id = _create_event_suggestion(admin_unit_id, freetext)
    result = {
        "event_suggestion_id": event_suggestion_id,
    }
    click.echo(json.dumps(result))


app.cli.add_command(test_cli)
