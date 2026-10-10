from datetime import datetime

import pytest

from project.dateutils import berlin_tz


def test_read(seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.incoming_event_reference",
        id=admin_unit_id,
        event_reference_id=reference_id,
    )
    utils.get_ok(url)


@pytest.mark.parametrize("db_error", [True, False])
def test_create(client, app, utils, seeder, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other Crew")
    event_id = seeder.create_event(other_admin_unit_id)

    url = utils.get_url("main.event_reference_create", event_id=event_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {"admin_unit_id": admin_unit_id},
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "main.event", event_id=event_id)

    with app.app_context():
        from project.models import EventReference

        reference = (
            EventReference.query.filter(EventReference.admin_unit_id == admin_unit_id)
            .filter(EventReference.event_id == event_id)
            .first()
        )
        assert reference is not None


def test_create_duplicateNotAllowed(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url("main.event_reference_create", event_id=event_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {"admin_unit_id": admin_unit_id},
    )
    utils.assert_response_ok(response)
    assert b"duplicate key" in response.data


def test_create_401(client, app, utils, seeder, mocker):
    seeder.create_user()
    seeder._utils.login()

    owner_id = seeder.create_user("owner@owner")
    other_admin_unit_id = seeder.create_admin_unit(owner_id, "Other Crew")
    event_id = seeder.create_event(other_admin_unit_id)

    url = utils.get_url("main.event_reference_create", event_id=event_id)
    response = client.get(url)
    assert response.status_code == 401


@pytest.mark.parametrize("db_error", [True, False])
def test_update(client, seeder, utils, app, db, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.incoming_event_reference_update",
        id=admin_unit_id,
        event_reference_id=reference_id,
    )
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "rating": 70,
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response,
        "manage_admin_unit.incoming_event_reference",
        id=admin_unit_id,
        event_reference_id=reference_id,
    )

    with app.app_context():
        from project.models import EventReference

        reference = db.session.get(EventReference, reference_id)
        assert reference.rating == 70


@pytest.mark.parametrize("db_error", [True, False])
def test_delete(client, seeder, utils, app, db, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.incoming_event_reference_delete",
        id=admin_unit_id,
        event_reference_id=reference_id,
    )
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {},
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.incoming_event_references", id=admin_unit_id
    )

    with app.app_context():
        from project.models import EventReference

        reference = db.session.get(EventReference, reference_id)
        assert reference is None


def test_admin_unit_references_incoming(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    utils.get_endpoint_ok(
        "manage_admin_unit.incoming_event_references", id=admin_unit_id
    )


def test_admin_unit_references_outgoing(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    seeder.create_reference(event_id, other_admin_unit_id)

    utils.get_endpoint_ok(
        "manage_admin_unit.outgoing_event_references", id=admin_unit_id
    )


def test_referencedEventUpdate_sendsMail(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")

    utils.logout()
    utils.login("other@test.de")

    # Event per Form anlegen, um dieselben Default-Werte wie im Update zu haben
    event_id = seeder.create_event_via_form(other_admin_unit_id)
    seeder.create_reference(event_id, admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_update", id=other_admin_unit_id, event_id=event_id
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Changed name",
        },
    )

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    assert (
        app.test_email_service.sent_emails[0]["subject"]
        == "Empfohlene Veranstaltung wurde geändert"
    )
    assert app.test_email_service.sent_emails[0]["recipient"] == "test@test.de"


def test_referencedEventNonDirtyUpdate_doesNotSendMail(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")

    utils.logout()
    utils.login("other@test.de")

    # Event per Form anlegen, um dieselben Default-Werte wie im Update zu haben
    event_id = seeder.create_event_via_form(other_admin_unit_id)
    seeder.create_reference(event_id, admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_update", id=other_admin_unit_id, event_id=event_id
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {},
    )

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    assert len(app.test_email_service.sent_emails) == 0


def test_referencedAlldayEventNonDirtyUpdate_doesNotSendMail(
    client, seeder, utils, app
):
    # Regression test: an untouched all-day event re-posted through the edit
    # form must not send a change notice, even though the form's time widget
    # has no seconds field and rounds the canonical 23:59:59 end down to
    # 23:59:00 on the round trip.
    import datetime

    from project.dateutils import berlin_tz

    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")

    utils.logout()
    utils.login("other@test.de")

    # Event per Form anlegen, um dieselben Default-Werte wie im Update zu haben
    event_id = seeder.create_event_via_form(other_admin_unit_id, allday=True)
    seeder.create_reference(event_id, admin_unit_id)

    with app.app_context():
        from project.models import Event

        event = Event.query.filter(Event.id == event_id).first()
        date_definition = event.date_definitions[0]
        assert date_definition.allday is True

        end_berlin = date_definition.end.astimezone(berlin_tz)
        assert end_berlin.date() == datetime.date(2030, 12, 31)
        assert (end_berlin.hour, end_berlin.minute, end_berlin.second) == (
            23,
            59,
            59,
        )

    url = utils.get_url(
        "manage_admin_unit.event_update", id=other_admin_unit_id, event_id=event_id
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {},
    )

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    assert len(app.test_email_service.sent_emails) == 0


def test_referencedAlldayEventNonDirtyUpdate_doesNotSendMail2(
    client, seeder, utils, app
):
    """An all-day end is stored as 23:59:59, but the form's time widget has no
    seconds and returns 23:59. Unless the value object widens it back, an
    untouched all-day event looks changed and sends a notice whose old and new
    dates render identically."""
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")

    utils.logout()
    utils.login("other@test.de")

    event_id = seeder.create_event_via_form(other_admin_unit_id, allday=True)
    seeder.create_reference(event_id, admin_unit_id)

    with app.app_context():
        from project.models import Event

        date_definition = Event.query.get(event_id).date_definitions[0]
        # Without these the test degrades into a copy of the one above as soon
        # as the seeder stops producing an all-day event, and still passes.
        assert date_definition.allday
        assert date_definition.end.astimezone(berlin_tz) == datetime(
            2030, 12, 31, 23, 59, 59, tzinfo=berlin_tz
        )

    url = utils.get_url(
        "manage_admin_unit.event_update", id=other_admin_unit_id, event_id=event_id
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {},
    )

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    assert len(app.test_email_service.sent_emails) == 0


def test_referencedRecurringEventChange_sendsMail_butDiffIsIndistinguishable(
    client, seeder, utils, app
):
    # Complementary case: here the recurrence rule genuinely changes (fewer
    # occurrences), so sending a mail is correct. But the notice only ever
    # renders "(Recurring event)" for a recurring definition -- never the
    # recurrence_rule content -- so the "before"/"after" lines print
    # identically even though the event's actual occurrences changed. The
    # recipient has no way to tell what changed from the mail alone.
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")

    utils.logout()
    utils.login("other@test.de")

    place_id = seeder.upsert_default_event_place(other_admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(other_admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_create", id=other_admin_unit_id)
    response = utils.get_ok(url)
    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "description": "Beschreibung",
            "date_definitions-0-start": ["2026-04-06", "11:00"],
            "date_definitions-0-recurrence_rule": "RRULE:FREQ=WEEKLY;COUNT=5",
            "event_place": place_id,
            "organizer": organizer_id,
            "photo-image_base64": seeder.get_default_image_upload_base64(),
            "photo-copyright_text": "EventCally",
        },
    )
    utils.assert_response_redirect(response, "main.event_actions", event_id=1)

    with app.app_context():
        from project.models import Event

        event = (
            Event.query.filter(Event.admin_unit_id == other_admin_unit_id)
            .filter(Event.name == "Name")
            .first()
        )
        event_id = event.id

    seeder.create_reference(event_id, admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_update", id=other_admin_unit_id, event_id=event_id
    )
    response = utils.get_ok(url)

    # A real change: five occurrences shrink to three.
    response = utils.post_form(
        url,
        response,
        {
            "date_definitions-0-recurrence_rule": "RRULE:FREQ=WEEKLY;COUNT=3",
        },
    )

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

        from project.models import Event

        event = Event.query.filter(Event.id == event_id).first()
        assert event.date_definitions[0].recurrence_rule == "RRULE:FREQ=WEEKLY;COUNT=3"

    assert len(app.test_email_service.sent_emails) == 1
    body = app.test_email_service.sent_emails[0]["body"]

    old_section = body.split("Termine (bisher):")[1].split("Termine (neu):")[0]
    new_section = body.split("Termine (neu):")[1]
    old_line = old_section.strip().splitlines()[0].strip()
    new_line = new_section.strip().splitlines()[0].strip()

    # The mail correctly reports that something changed (COUNT=5 -> COUNT=3
    # is a real, meaningful difference), but the rendered lines are
    # byte-identical: the recipient cannot tell what actually changed.
    assert old_line == new_line == "- 06.04.26 11:00 (Serientermin)"
