import pytest


def test_event_validate_organizer(client, app):
    with app.app_context():
        from sqlalchemy.exc import IntegrityError

        from project.infrastructure.models import Event, EventOrganizer

        event = Event()
        event.admin_unit_id = 1
        event.organizer = EventOrganizer(admin_unit_id=2, name="Org")

        with pytest.raises(IntegrityError) as e:
            event.validate()
        assert e.value.orig.message == "Invalid organizer."


def test_event_validate_place(client, app):
    with app.app_context():
        from sqlalchemy.exc import IntegrityError

        from project.infrastructure.models import Event, EventPlace

        event = Event()
        event.admin_unit_id = 1
        event.event_place = EventPlace(admin_unit_id=2, name="Place")

        with pytest.raises(IntegrityError) as e:
            event.validate()
        assert e.value.orig.message == "Invalid place."


def test_event_validate_co_organizer(client, app):
    with app.app_context():
        from sqlalchemy.exc import IntegrityError

        from project.infrastructure.models import Event, EventOrganizer

        event = Event()
        event.admin_unit_id = 1
        event.co_organizers = [
            EventOrganizer(admin_unit_id=2, name="Org1"),
            EventOrganizer(admin_unit_id=1, name="Org2"),
        ]

        with pytest.raises(IntegrityError) as e:
            event.validate()
        assert e.value.orig.message == "Invalid co-organizer."


def test_event_without_date_definitions(app):
    from project.infrastructure.models import Event

    event = Event()

    assert event.min_start_definition is None
    assert event.min_start is None
    assert event.is_recurring is False
    assert event.category is None
    assert event.has_multiple_dates() is False


def test_event_with_date_definitions(app):
    import datetime

    from project.infrastructure.models import Event, EventDateDefinition

    early = datetime.datetime(2030, 1, 1, tzinfo=datetime.UTC)
    late = datetime.datetime(2030, 2, 1, tzinfo=datetime.UTC)
    event = Event()
    event.date_definitions = [
        EventDateDefinition(start=late),
        EventDateDefinition(start=early, recurrence_rule="RRULE:FREQ=DAILY;COUNT=2"),
    ]

    assert event.min_start_definition.start == early
    assert event.min_start == early
    assert event.is_recurring is True
    assert event.has_multiple_dates() is True


def test_event_validate_requires_a_date_definition(app):
    import pytest
    from sqlalchemy.exc import IntegrityError

    from project.infrastructure.models import Event

    with pytest.raises(IntegrityError) as e:
        Event().validate()
    assert e.value.orig.message == "At least one date defintion is required."


def test_fill_from_aggregate_drops_removed_date_definitions(app, db, seeder):
    import datetime
    from zoneinfo import ZoneInfo

    from project.domain.models.value_objects.event_date_definition_value_object import (
        EventDateDefinitionValueObject,
    )
    from project.infrastructure.models import Event

    _, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(
        admin_unit_id, start=datetime.datetime(2030, 1, 1, 10, 0)
    )
    seeder.add_event_date_definition(event_id, datetime.datetime(2030, 2, 1, 10, 0))

    with app.app_context():
        from project.infrastructure.repositories.sql_alchemy_event_repository import (
            SqlAlchemyEventRepository,
        )

        repo = SqlAlchemyEventRepository(db.session)
        aggregate = repo.get(event_id)
        assert len(aggregate.date_definitions) == 2

        aggregate.date_definitions = [
            EventDateDefinitionValueObject(
                start=datetime.datetime(2030, 3, 1, 10, 0, tzinfo=ZoneInfo("UTC"))
            )
        ]
        event = db.session.get(Event, event_id)
        event.fill_from_aggregate(aggregate)
        db.session.commit()

        db.session.expire_all()
        assert len(db.session.get(Event, event_id).date_definitions) == 1
