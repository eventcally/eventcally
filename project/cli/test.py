import json

import click
from flask.cli import AppGroup
from flask_migrate import stamp
from flask_security.confirmable import confirm_user
from sqlalchemy import MetaData

from project import app, db
from project.api import scope_list
from project.init_data import create_initial_data
from project.models import (
    AdminUnit,
    AdminUnitInvitation,
    Event,
    EventAttendanceMode,
    EventDateDefinition,
    EventList,
    EventReference,
    EventReferenceRequest,
    EventReferenceRequestReviewStatus,
    EventSuggestion,
    Location,
    OAuth2Client,
)
from project.services.admin_unit import (
    add_user_to_admin_unit_with_roles,
    get_admin_unit_by_id,
    insert_admin_unit_for_user,
    insert_admin_unit_member_invitation,
    upsert_admin_unit_relation,
)
from project.services.event import insert_event, upsert_event_category
from project.services.event_suggestion import insert_event_suggestion
from project.services.oauth2_client import complete_oauth2_client
from project.services.organizer import get_event_organizer, upsert_event_organizer
from project.services.place import get_event_places, upsert_event_place
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
    db.engine.execute("DROP TABLE IF EXISTS alembic_version;")
    click.echo("Drop all done.")


@test_cli.command("create-all")
def create_all():
    stamp()
    db.create_all()
    click.echo("Create all done.")


@test_cli.command("seed")
def seed():
    create_initial_data()
    click.echo("Seed done.")


def _verify_admin_unit(admin_unit_id):
    from project.services.admin_unit import get_admin_unit_by_name

    other_admin_unit = get_admin_unit_by_name("eventcally")

    if other_admin_unit:
        other_admin_unit_id = other_admin_unit.id
    else:
        other_user_id = _create_user("unverified@test.de")
        other_admin_unit_id = _create_admin_unit(other_user_id, "eventcally")

    _create_admin_unit_relation(
        other_admin_unit_id,
        admin_unit_id,
        verify=True,
    )


def _create_admin_unit(user_id, name, verified=False):
    user = get_user(user_id)

    admin_unit = AdminUnit()
    admin_unit.name = name
    admin_unit.short_name = name.lower().replace(" ", "")
    admin_unit.incoming_reference_requests_allowed = True
    admin_unit.suggestions_enabled = True
    admin_unit.can_create_other = True
    admin_unit.can_verify_other = True
    admin_unit.can_invite_other = True
    admin_unit.location = Location()
    admin_unit.location.postalCode = "38640"
    admin_unit.location.city = "Goslar"
    insert_admin_unit_for_user(admin_unit, user)
    db.session.commit()

    if verified:
        _verify_admin_unit(admin_unit.id)

    return admin_unit.id


@test_cli.command("admin-unit-create")
@click.argument("user_email")
@click.argument("name", default="Meine Crew")
def create_admin_unit(user_email, name):
    user = find_user_by_email(user_email)
    admin_unit_id = _create_admin_unit(user.id, name, verified=True)
    result = {"admin_unit_id": admin_unit_id}
    click.echo(json.dumps(result))


@test_cli.command("admin-unit-member-invitation-create")
@click.argument("admin_unit_id")
@click.argument("email")
def create_admin_unit_member_invitation(admin_unit_id, email):
    invitation = insert_admin_unit_member_invitation(admin_unit_id, email, [])
    result = {"invitation_id": invitation.id}
    click.echo(json.dumps(result))


@test_cli.command("admin-unit-member-create")
@click.argument("admin_unit_id")
@click.argument("user_email")
def create_admin_unit_member(admin_unit_id, user_email):
    user = find_user_by_email(user_email)
    admin_unit = get_admin_unit_by_id(admin_unit_id)
    member = add_user_to_admin_unit_with_roles(user, admin_unit, [])
    db.session.commit()
    result = {"member_id": member.id}
    click.echo(json.dumps(result))


def _create_event(admin_unit_id):
    event = Event()
    event.admin_unit_id = admin_unit_id
    event.categories = [upsert_event_category("Other")]
    event.name = "Name"
    event.description = "Beschreibung"
    event.event_place_id = _get_default_event_place_id(admin_unit_id)
    event.organizer_id = _get_default_organizer_id(admin_unit_id)
    event.ticket_link = ""
    event.tags = ""
    event.price_info = ""
    event.attendance_mode = EventAttendanceMode.offline

    date_definition = EventDateDefinition()
    date_definition.start = _get_now_by_minute()
    event.date_definitions = [date_definition]

    insert_event(event)
    db.session.commit()

    return event.id


@test_cli.command("event-create")
@click.argument("admin_unit_id")
def create_event(admin_unit_id):
    event_id = _create_event(admin_unit_id)
    result = {"event_id": event_id}
    click.echo(json.dumps(result))


@test_cli.command("event-place-create")
@click.argument("admin_unit_id")
@click.argument("name")
def create_event_place(admin_unit_id, name):
    event_place = upsert_event_place(admin_unit_id, name)
    db.session.commit()
    result = {"event_place_id": event_place.id}
    click.echo(json.dumps(result))


@test_cli.command("event-organizer-create")
@click.argument("admin_unit_id")
@click.argument("name")
def create_event_organizer(admin_unit_id, name):
    event_organizer = upsert_event_organizer(admin_unit_id, name)
    db.session.commit()
    result = {"event_organizer_id": event_organizer.id}
    click.echo(json.dumps(result))


def _insert_default_oauth2_client(user_id):
    client = OAuth2Client()
    client.user_id = user_id
    complete_oauth2_client(client)

    metadata = dict()
    metadata["client_name"] = "Mein Client"
    metadata["scope"] = " ".join(scope_list)
    metadata["grant_types"] = ["authorization_code", "refresh_token"]
    metadata["response_types"] = ["code"]
    metadata["token_endpoint_auth_method"] = "client_secret_post"
    metadata["redirect_uris"] = ["/"]
    client.set_client_metadata(metadata)

    db.session.add(client)
    db.session.commit()

    return client


@test_cli.command("oauth2-client-create")
@click.argument("user_id")
def create_oauth2_client(user_id):
    oauth2_client = _insert_default_oauth2_client(user_id)
    result = {
        "oauth2_client_id": oauth2_client.id,
        "oauth2_client_client_id": oauth2_client.client_id,
        "oauth2_client_secret": oauth2_client.client_secret,
        "oauth2_client_scope": oauth2_client.scope,
    }
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


def _create_reference(event_id, admin_unit_id):
    reference = EventReference()
    reference.event_id = event_id
    reference.admin_unit_id = admin_unit_id
    db.session.add(reference)
    db.session.commit()
    return reference.id


def _create_incoming_reference(admin_unit_id):
    other_user_id = _create_user("other@test.de")
    other_admin_unit_id = _create_admin_unit(other_user_id, "Other Crew")
    event_id = _create_event(other_admin_unit_id)
    reference_id = _create_reference(event_id, admin_unit_id)
    return (other_user_id, other_admin_unit_id, event_id, reference_id)


@test_cli.command("reference-create-incoming")
@click.argument("admin_unit_id")
def create_incoming_request(admin_unit_id):
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = _create_incoming_reference(admin_unit_id)
    result = {
        "other_user_id": other_user_id,
        "other_admin_unit_id": other_admin_unit_id,
        "event_id": event_id,
        "reference_id": reference_id,
    }
    click.echo(json.dumps(result))


def _create_admin_unit_relation(
    admin_unit_id,
    target_admin_unit_id,
    auto_verify_event_reference_requests=False,
    verify=False,
):
    relation = upsert_admin_unit_relation(admin_unit_id, target_admin_unit_id)
    relation.auto_verify_event_reference_requests = auto_verify_event_reference_requests
    relation.verify = verify
    db.session.commit()
    return relation.id


def _create_any_admin_unit_relation(admin_unit_id):
    other_user_id = _create_user("other@test.de")
    other_admin_unit_id = _create_admin_unit(other_user_id, "Other Crew")
    relation_id = _create_admin_unit_relation(admin_unit_id, other_admin_unit_id)
    return (other_user_id, other_admin_unit_id, relation_id)


@test_cli.command("admin-unit-relation-create")
@click.argument("admin_unit_id")
def create_admin_unit_relation(admin_unit_id):
    (
        other_user_id,
        other_admin_unit_id,
        relation_id,
    ) = _create_any_admin_unit_relation(admin_unit_id)
    result = {
        "other_user_id": other_user_id,
        "other_admin_unit_id": other_admin_unit_id,
        "relation_id": relation_id,
    }
    click.echo(json.dumps(result))


def _create_admin_unit_invitation(
    admin_unit_id,
    email="invited@test.de",
    admin_unit_name="Invited Organization",
):
    invitation = AdminUnitInvitation()
    invitation.admin_unit_id = admin_unit_id
    invitation.email = email
    invitation.admin_unit_name = admin_unit_name
    db.session.add(invitation)
    db.session.commit()
    return invitation.id


@test_cli.command("admin-unit-organization-invitation-create")
@click.argument("admin_unit_id")
@click.argument("email")
def create_admin_unit_organization_invitation(admin_unit_id, email):
    invitation_id = _create_admin_unit_invitation(admin_unit_id, email)
    result = {
        "invitation_id": invitation_id,
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


def _add_event_to_list(event_list_id, event_id):
    event = Event.query.get(event_id)
    event_list = EventList.query.get(event_list_id)
    event_list.events.append(event)
    db.session.commit()


def _create_event_list(admin_unit_id, event_ids=list(), name="My list"):
    event_list = EventList()
    event_list.name = name
    event_list.admin_unit_id = admin_unit_id
    db.session.add(event_list)
    db.session.commit()
    event_list_id = event_list.id

    if type(event_ids) is not list:
        event_ids = [event_ids]

    for event_id in event_ids:
        _add_event_to_list(event_list_id, event_id)

    return event_list_id


@test_cli.command("event-list-create")
@click.argument("admin_unit_id")
def create_event_list(admin_unit_id):
    event_list_id = _create_event_list(admin_unit_id)
    result = {
        "event_list_id": event_list_id,
    }
    click.echo(json.dumps(result))


app.cli.add_command(test_cli)
