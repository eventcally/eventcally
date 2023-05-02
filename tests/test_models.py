import pytest

from tests.seeder import Seeder


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

        event = db.session.get(Event, event_id)
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
        event = db.session.get(Event, event_with_start_id)
        date_definition = event.date_definitions[0]
        assert date_definition.allday
        assert date_definition.start == create_berlin_date(2030, 12, 31, 0, 0)
        assert date_definition.end == create_berlin_date(2030, 12, 31, 23, 59, 59)

        event_date = event.dates[0]
        assert event_date.allday
        assert event_date.start == create_berlin_date(2030, 12, 31, 0, 0)
        assert event_date.end == create_berlin_date(2030, 12, 31, 23, 59, 59)

        # With Start and End
        event = db.session.get(Event, event_with_start_and_end_id)
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

        event_with_recc = db.session.get(Event, event_with_recc_id)
        assert event_with_recc.has_multiple_dates() is True

        event_without_recc = db.session.get(Event, event_without_recc_id)
        assert event_without_recc.has_multiple_dates() is False


def test_oauth2_token(client, app, seeder):
    import time

    from project.models import OAuth2Token

    token = OAuth2Token()
    token.access_token_revoked_at = int(time.time())
    assert not token.is_refresh_token_active()

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
        from project.models import Event, EventDateDefinition

        # Initial eine Definition
        event = db.session.get(Event, event_id)
        assert len(event.date_definitions) == 1
        date_definition1 = event.date_definitions[0]

        # Zweite Definition hinzufügen
        date_definition2 = seeder.create_event_date_definition()
        db.session.add(date_definition2)
        event.date_definitions = [date_definition1, date_definition2]
        db.session.commit()

        event = db.session.get(Event, event_id)
        assert len(event.date_definitions) == 2
        assert len(EventDateDefinition.query.all()) == 2

        # Erste Definition löschen
        date_definition1, date_definition2 = event.date_definitions
        date_definition2_id = date_definition2.id

        db.session.delete(date_definition1)
        db.session.commit()

        event = db.session.get(Event, event_id)
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
        my_event = db.session.get(Event, my_event_id)
        date_id = my_event.dates[0].id
        date_definition_id = my_event.date_definitions[0].id

        db.session.delete(admin_unit)
        db.session.commit()
        assert len(other_admin_unit.outgoing_relations) == 0

        assert db.session.get(Event, my_event_id) is None
        assert db.session.get(EventDate, date_id) is None
        assert db.session.get(EventDateDefinition, date_definition_id) is None
        assert db.session.get(AdminUnitRelation, incoming_relation_id) is None
        assert db.session.get(AdminUnitRelation, outgoing_relation_id) is None
        assert db.session.get(EventReference, incoming_reference_id) is None
        assert db.session.get(EventReference, outgoing_reference_id) is None
        assert (
            db.session.get(EventReferenceRequest, incoming_reference_request_id) is None
        )
        assert (
            db.session.get(EventReferenceRequest, outgoing_reference_request_id) is None
        )
        assert db.session.get(EventSuggestion, suggestion_id) is None
        assert db.session.get(EventPlace, event_place_id) is None
        assert db.session.get(EventOrganizer, organizer_id) is None
        assert db.session.get(AdminUnitMemberInvitation, invitation_id) is None
        assert db.session.get(EventList, event_list_id) is None

        assert db.session.get(AdminUnit, other_admin_unit_id) is not None
        assert db.session.get(Event, other_event_id) is not None


def test_event_co_organizers_deletion(client, app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id, organizer_a_id, organizer_b_id = seeder.create_event_with_co_organizers(
        admin_unit_id
    )

    with app.app_context():
        from project.models import Event, EventOrganizer

        event = db.session.get(Event, event_id)
        assert len(event.co_organizers) == 2
        assert event.co_organizers[0].id == organizer_a_id
        assert event.co_organizers[1].id == organizer_b_id

        organizer_a = db.session.get(EventOrganizer, organizer_a_id)
        db.session.delete(organizer_a)
        db.session.commit()
        assert len(event.co_organizers) == 1
        assert event.co_organizers[0].id == organizer_b_id

        db.session.delete(event)
        db.session.commit()
        assert db.session.get(EventOrganizer, organizer_b_id).id is not None


def test_admin_unit_verification(client, app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False, admin_unit_verified=False)
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")

    with app.app_context():
        from project.models import AdminUnit, AdminUnitRelation

        new_admin_unit = AdminUnit()
        assert not new_admin_unit.is_verified

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.can_verify_other = True
        db.session.commit()

        relation_id = seeder.create_admin_unit_relation(
            admin_unit_id, other_admin_unit_id
        )

        all_verified = AdminUnit.query.filter(AdminUnit.is_verified).all()
        assert len(all_verified) == 0

        relation = db.session.get(AdminUnitRelation, relation_id)
        relation.verify = True
        db.session.commit()

        other_admin_unit = db.session.get(AdminUnit, other_admin_unit_id)
        assert other_admin_unit.is_verified

        all_verified = AdminUnit.query.filter(AdminUnit.is_verified).all()
        assert len(all_verified) == 1
        assert all_verified[0].id == other_admin_unit_id

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
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
        invitation = db.session.get(AdminUnitInvitation, invitation_id)
        assert invitation is None


def test_event_list_deletion(client, app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    event_list_a_id = seeder.create_event_list(admin_unit_id, event_id, "List A")
    event_list_b_id = seeder.create_event_list(admin_unit_id, event_id, "List B")

    with app.app_context():
        from project.models import Event, EventList

        event_list_a = db.session.get(EventList, event_list_a_id)
        assert len(event_list_a.events) == 1
        assert event_list_a.events[0].id == event_id

        event_list_b = db.session.get(EventList, event_list_b_id)
        assert len(event_list_b.events) == 1
        assert event_list_b.events[0].id == event_id

        event = db.session.get(Event, event_id)
        assert len(event.event_lists) == 2
        assert event.event_lists[0].id == event_list_a_id
        assert event.event_lists[1].id == event_list_b_id

        event_list_a = db.session.get(EventList, event_list_a_id)
        db.session.delete(event_list_a)
        db.session.commit()
        assert len(event.event_lists) == 1
        assert event.event_lists[0].id == event_list_b_id

        event_list_b = db.session.get(EventList, event_list_b_id)
        assert len(event_list_b.events) == 1
        assert event_list_b.events[0].id == event_id

        db.session.delete(event)
        db.session.commit()

        event_list_b = db.session.get(EventList, event_list_b_id)
        assert len(event_list_b.events) == 0


def test_event_is_favored_by_current_user(client, app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.models import Event

        event = db.session.get(Event, event_id)
        assert event.is_favored_by_current_user() is False


def test_purge_event_photo(client, app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    first_image_id = seeder.upsert_default_image()
    seeder.assign_image_to_event(event_id, first_image_id)

    with app.app_context():
        from project.models import Event, Image

        event = db.session.get(Event, event_id)
        assert event.photo is not None

        event.photo.data = None
        db.session.commit()

        event = db.session.get(Event, event_id)
        assert event.photo is None

        image = db.session.get(Image, first_image_id)
        assert image is None


def test_purge_event_place_photo(client, app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    first_image_id = seeder.upsert_default_image()
    second_image_id = seeder.upsert_default_image()

    with app.app_context():
        from project.models import EventPlace, Image

        place = db.session.get(EventPlace, place_id)
        place.photo = db.session.get(Image, first_image_id)
        db.session.commit()

        assert place.photo is not None

        place.photo = db.session.get(Image, second_image_id)
        db.session.commit()

        place = db.session.get(EventPlace, place_id)
        assert place.photo is not None

        image = db.session.get(Image, first_image_id)
        assert image is None

        image = db.session.get(Image, second_image_id)
        assert image is not None

        place.photo.data = None
        db.session.commit()

        place = db.session.get(EventPlace, place_id)
        assert place.photo is None

        image = db.session.get(Image, second_image_id)
        assert image is None


def test_purge_eventsuggestion_photo(client, app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    suggestion_id = seeder.create_event_suggestion(admin_unit_id)
    image_id = seeder.upsert_default_image()

    with app.app_context():
        from project.models import EventSuggestion, Image

        suggestion = db.session.get(EventSuggestion, suggestion_id)
        suggestion.photo = db.session.get(Image, image_id)
        db.session.commit()

        assert suggestion.photo is not None

        suggestion.photo.data = None
        db.session.commit()

        suggestion = db.session.get(EventSuggestion, suggestion_id)
        assert suggestion.photo is None

        image = db.session.get(Image, image_id)
        assert image is None


def test_purge_adminunit(client, app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    instance_id = admin_unit_id
    image_id = seeder.upsert_default_image()
    location_id = seeder.create_location(street="Street")

    with app.app_context():
        from project.models import AdminUnit, Image, Location

        instance = db.session.get(AdminUnit, instance_id)
        instance.logo = db.session.get(Image, image_id)
        instance.location = db.session.get(Location, location_id)
        db.session.commit()

        assert instance.logo is not None
        assert instance.location is not None

        instance.logo.data = None
        instance.location.street = None
        db.session.commit()

        instance = db.session.get(AdminUnit, instance_id)
        assert instance.logo is None
        assert instance.location is None

        image = db.session.get(Image, image_id)
        assert image is None

        location = db.session.get(Location, location_id)
        assert location is None


def test_purge_eventorganizer(client, app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    instance_id = seeder.upsert_default_event_organizer(admin_unit_id)
    image_id = seeder.upsert_default_image()
    location_id = seeder.create_location(street="Street")

    with app.app_context():
        from project.models import EventOrganizer, Image, Location

        instance = db.session.get(EventOrganizer, instance_id)
        instance.logo = db.session.get(Image, image_id)
        instance.location = db.session.get(Location, location_id)
        db.session.commit()

        assert instance.logo is not None
        assert instance.location is not None

        instance.logo.data = None
        instance.location.street = None
        db.session.commit()

        instance = db.session.get(EventOrganizer, instance_id)
        assert instance.logo is None
        assert instance.location is None

        image = db.session.get(Image, image_id)
        assert image is None

        location = db.session.get(Location, location_id)
        assert location is None


def test_delete_admin_unit(client, app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    instance_id = seeder.upsert_default_event_organizer(admin_unit_id)
    image_id = seeder.upsert_default_image()
    location_id = seeder.create_location(street="Street")

    with app.app_context():
        from project.models import AdminUnit, EventOrganizer, Image, Location
        from project.services.admin_unit import delete_admin_unit

        instance = db.session.get(EventOrganizer, instance_id)
        instance.logo = db.session.get(Image, image_id)
        instance.location = db.session.get(Location, location_id)
        db.session.commit()

        assert instance.logo is not None
        assert instance.location is not None

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        delete_admin_unit(admin_unit)

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        assert admin_unit is None

        image = db.session.get(Image, image_id)
        assert image is None

        location = db.session.get(Location, location_id)
        assert admin_unit is location


def test_delete_user(client, app, db, seeder: Seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id, created_by_id=user_id)

    with app.app_context():
        from project.models import AdminUnit, AdminUnitMember, Event, User
        from project.services.user import delete_user

        user = db.session.get(User, user_id)
        member_id = user.adminunitmembers[0].id
        delete_user(user)

        # User and membership should be gone
        assert db.session.get(User, user_id) is None
        assert db.session.get(AdminUnitMember, member_id) is None

        # Admin unit and event should still be there
        assert db.session.get(AdminUnit, admin_unit_id) is not None
        event = db.session.get(Event, event_id)
        event is not None
        event.created_by_id is None
