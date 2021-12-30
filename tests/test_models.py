import pytest

from project.models import EventDateDefinition


def test_location_update_coordinate(client, app, db):
    from project.models import Location

    location = Location()
    location.latitude = 51.9077888
    location.longitude = 10.4333312
    location.update_coordinate()

    assert location.coordinate is not None


def test_event_category(client, app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.models import Event

        event = Event.query.get(event_id)
        event.categories = []
        db.session.commit()

        assert event.category is None


def test_event_properties(client, app, db, seeder):
    with app.app_context():
        from sqlalchemy.exc import IntegrityError

        from project.dateutils import create_berlin_date
        from project.models import Event, EventDateDefinition

        event = Event()
        assert event.min_start_definition is None
        assert event.min_start is None
        assert event.is_recurring is False

        with pytest.raises(IntegrityError) as e:
            event.validate()
        assert e.value.orig.message == "At least one date defintion is required."

        start = create_berlin_date(2030, 12, 31, 14, 30)
        date_definition = EventDateDefinition()
        date_definition.start = start
        event.date_definitions = [date_definition]
        assert event.min_start == start


def test_event_allday(client, app, db, seeder):
    from project.dateutils import create_berlin_date

    user_id, admin_unit_id = seeder.setup_base()
    event_with_start_id = seeder.create_event(
        admin_unit_id, allday=True, start=create_berlin_date(2030, 12, 31, 14, 30)
    )
    event_with_start_and_end_id = seeder.create_event(
        admin_unit_id,
        allday=True,
        start=create_berlin_date(2030, 12, 31, 14, 30),
        end=create_berlin_date(2031, 1, 1, 0, 0),
    )

    with app.app_context():
        from project.models import Event

        # With Start
        event = Event.query.get(event_with_start_id)
        date_definition = event.date_definitions[0]
        assert date_definition.allday
        assert date_definition.start == create_berlin_date(2030, 12, 31, 0, 0)
        assert date_definition.end == create_berlin_date(2030, 12, 31, 23, 59, 59)

        event_date = event.dates[0]
        assert event_date.allday
        assert event_date.start == create_berlin_date(2030, 12, 31, 0, 0)
        assert event_date.end == create_berlin_date(2030, 12, 31, 23, 59, 59)

        # With Start and End
        event = Event.query.get(event_with_start_and_end_id)
        date_definition = event.date_definitions[0]
        assert date_definition.allday
        assert date_definition.start == create_berlin_date(2030, 12, 31, 0, 0)
        assert date_definition.end == create_berlin_date(2031, 1, 1, 23, 59, 59)

        event_date = event.dates[0]
        assert event_date.allday
        assert event_date.start == create_berlin_date(2030, 12, 31, 0, 0)
        assert event_date.end == create_berlin_date(2031, 1, 1, 23, 59, 59)


def test_event_has_multiple_dates(client, app, db, seeder):
    _, admin_unit_id = seeder.setup_base()
    event_with_recc_id = seeder.create_event(
        admin_unit_id, recurrence_rule="RRULE:FREQ=DAILY;COUNT=7"
    )
    event_without_recc_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.models import Event

        event_with_recc = Event.query.get(event_with_recc_id)
        assert event_with_recc.has_multiple_dates() is True

        event_without_recc = Event.query.get(event_without_recc_id)
        assert event_without_recc.has_multiple_dates() is False


def test_oauth2_token(client, app):
    from project.models import OAuth2Token

    token = OAuth2Token()
    token.revoked = True
    assert not token.is_refresh_token_active()

    token.revoked = False
    token.issued_at = 0
    token.expires_in = 0
    assert not token.is_refresh_token_active()


def test_admin_unit_relations(client, app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    (
        other_user_id,
        other_admin_unit_id,
        relation_id,
    ) = seeder.create_any_admin_unit_relation(admin_unit_id)

    with app.app_context():
        from project.services.admin_unit import get_admin_unit_by_id

        admin_unit = get_admin_unit_by_id(admin_unit_id)
        assert len(admin_unit.outgoing_relations) == 1
        relation = admin_unit.outgoing_relations[0]
        assert relation.id == relation_id

        db.session.delete(relation)
        db.session.commit()
        assert len(admin_unit.outgoing_relations) == 0


def test_event_date_defintion_deletion(client, app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.models import Event

        # Initial eine Definition
        event = Event.query.get(event_id)
        assert len(event.date_definitions) == 1
        date_definition1 = event.date_definitions[0]

        # Zweite Definition hinzufügen
        date_definition2 = seeder.create_event_date_definition()
        db.session.add(date_definition2)
        event.date_definitions = [date_definition1, date_definition2]
        db.session.commit()

        event = Event.query.get(event_id)
        assert len(event.date_definitions) == 2
        assert len(EventDateDefinition.query.all()) == 2

        # Erste Definition löschen
        date_definition1, date_definition2 = event.date_definitions
        date_definition2_id = date_definition2.id

        db.session.delete(date_definition1)
        db.session.commit()

        event = Event.query.get(event_id)
        assert len(event.date_definitions) == 1
        assert len(EventDateDefinition.query.all()) == 1
        assert event.date_definitions[0].id == date_definition2_id


def test_admin_unit_deletion(client, app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    my_event_id = seeder.create_event(admin_unit_id)
    suggestion_id = seeder.create_event_suggestion(admin_unit_id)
    event_place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    invitation_id = seeder.create_invitation(admin_unit_id, "newbie@domain.com")
    event_list_id = seeder.create_event_list(admin_unit_id, my_event_id)

    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    other_event_id = seeder.create_event(other_admin_unit_id)
    incoming_reference_request_id = seeder.create_reference_request(
        other_event_id, admin_unit_id
    )
    outgoing_reference_request_id = seeder.create_reference_request(
        my_event_id, other_admin_unit_id
    )
    incoming_relation_id = seeder.create_admin_unit_relation(
        other_admin_unit_id, admin_unit_id
    )
    outgoing_relation_id = seeder.create_admin_unit_relation(
        admin_unit_id, other_admin_unit_id
    )
    incoming_reference_id = seeder.create_reference(other_event_id, admin_unit_id)
    outgoing_reference_id = seeder.create_reference(my_event_id, other_admin_unit_id)

    with app.app_context():
        from project.models import (
            AdminUnit,
            AdminUnitMemberInvitation,
            AdminUnitRelation,
            Event,
            EventDate,
            EventDateDefinition,
            EventList,
            EventOrganizer,
            EventPlace,
            EventReference,
            EventReferenceRequest,
            EventSuggestion,
        )
        from project.services.admin_unit import get_admin_unit_by_id

        admin_unit = get_admin_unit_by_id(admin_unit_id)
        other_admin_unit = get_admin_unit_by_id(other_admin_unit_id)
        my_event = Event.query.get(my_event_id)
        date_id = my_event.dates[0].id
        date_definition_id = my_event.date_definitions[0].id

        db.session.delete(admin_unit)
        db.session.commit()
        assert len(other_admin_unit.outgoing_relations) == 0

        assert Event.query.get(my_event_id) is None
        assert EventDate.query.get(date_id) is None
        assert EventDateDefinition.query.get(date_definition_id) is None
        assert AdminUnitRelation.query.get(incoming_relation_id) is None
        assert AdminUnitRelation.query.get(outgoing_relation_id) is None
        assert EventReference.query.get(incoming_reference_id) is None
        assert EventReference.query.get(outgoing_reference_id) is None
        assert EventReferenceRequest.query.get(incoming_reference_request_id) is None
        assert EventReferenceRequest.query.get(outgoing_reference_request_id) is None
        assert EventSuggestion.query.get(suggestion_id) is None
        assert EventPlace.query.get(event_place_id) is None
        assert EventOrganizer.query.get(organizer_id) is None
        assert AdminUnitMemberInvitation.query.get(invitation_id) is None
        assert EventList.query.get(event_list_id) is None

        assert AdminUnit.query.get(other_admin_unit_id) is not None
        assert Event.query.get(other_event_id) is not None


def test_event_co_organizers_deletion(client, app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id, organizer_a_id, organizer_b_id = seeder.create_event_with_co_organizers(
        admin_unit_id
    )

    with app.app_context():
        from project.models import Event, EventOrganizer

        event = Event.query.get(event_id)
        assert len(event.co_organizers) == 2
        assert event.co_organizers[0].id == organizer_a_id
        assert event.co_organizers[1].id == organizer_b_id

        organizer_a = EventOrganizer.query.get(organizer_a_id)
        db.session.delete(organizer_a)
        db.session.commit()
        assert len(event.co_organizers) == 1
        assert event.co_organizers[0].id == organizer_b_id

        db.session.delete(event)
        db.session.commit()
        assert EventOrganizer.query.get(organizer_b_id).id is not None


def test_admin_unit_verification(client, app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False, admin_unit_verified=False)
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")

    with app.app_context():
        from project.models import AdminUnit, AdminUnitRelation

        new_admin_unit = AdminUnit()
        assert not new_admin_unit.is_verified

        admin_unit = AdminUnit.query.get(admin_unit_id)
        admin_unit.can_verify_other = True
        db.session.commit()

        relation_id = seeder.create_admin_unit_relation(
            admin_unit_id, other_admin_unit_id
        )

        all_verified = AdminUnit.query.filter(AdminUnit.is_verified).all()
        assert len(all_verified) == 0

        relation = AdminUnitRelation.query.get(relation_id)
        relation.verify = True
        db.session.commit()

        other_admin_unit = AdminUnit.query.get(other_admin_unit_id)
        assert other_admin_unit.is_verified

        all_verified = AdminUnit.query.filter(AdminUnit.is_verified).all()
        assert len(all_verified) == 1
        assert all_verified[0].id == other_admin_unit_id

        admin_unit = AdminUnit.query.get(admin_unit_id)
        admin_unit.can_verify_other = False
        db.session.commit()

        all_verified = AdminUnit.query.filter(AdminUnit.is_verified).all()
        assert len(all_verified) == 0


def test_admin_unit_invitations(client, app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    with app.app_context():
        from project.models import AdminUnitInvitation
        from project.services.admin_unit import get_admin_unit_by_id

        admin_unit = get_admin_unit_by_id(admin_unit_id)
        assert len(admin_unit.admin_unit_invitations) == 1

        admin_unit.can_invite_other = False
        db.session.commit()

        assert len(admin_unit.admin_unit_invitations) == 0
        invitation = AdminUnitInvitation.query.get(invitation_id)
        assert invitation is None


def test_event_list_deletion(client, app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    event_list_a_id = seeder.create_event_list(admin_unit_id, event_id, "List A")
    event_list_b_id = seeder.create_event_list(admin_unit_id, event_id, "List B")

    with app.app_context():
        from project.models import Event, EventList

        event_list_a = EventList.query.get(event_list_a_id)
        assert len(event_list_a.events) == 1
        assert event_list_a.events[0].id == event_id

        event_list_b = EventList.query.get(event_list_b_id)
        assert len(event_list_b.events) == 1
        assert event_list_b.events[0].id == event_id

        event = Event.query.get(event_id)
        assert len(event.event_lists) == 2
        assert event.event_lists[0].id == event_list_a_id
        assert event.event_lists[1].id == event_list_b_id

        event_list_a = EventList.query.get(event_list_a_id)
        db.session.delete(event_list_a)
        db.session.commit()
        assert len(event.event_lists) == 1
        assert event.event_lists[0].id == event_list_b_id

        event_list_b = EventList.query.get(event_list_b_id)
        assert len(event_list_b.events) == 1
        assert event_list_b.events[0].id == event_id

        db.session.delete(event)
        db.session.commit()

        event_list_b = EventList.query.get(event_list_b_id)
        assert len(event_list_b.events) == 0
