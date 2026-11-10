import pytest

from project.domain.errors import DuplicateError
from project.domain.models.aggregates.calendar_aggregate import CalendarAggregate
from project.domain.models.aggregates.calendar_entry_aggregate import (
    CalendarEntryAggregate,
)
from project.domain.models.entities.actor import Actor
from project.infrastructure.repositories.sql_alchemy_calendar_entry_repository import (
    SqlAlchemyCalendarEntryRepository,
)
from project.infrastructure.repositories.sql_alchemy_calendar_repository import (
    SqlAlchemyCalendarRepository,
)


def test_add_get_update_remove(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    actor = Actor(user_id=user_id)
    with app.app_context():
        repo = SqlAlchemyCalendarRepository(db.session)
        calendar = CalendarAggregate.create(
            actor=actor,
            admin_unit_id=admin_unit_id,
            name="Sports",
            description="Text",
            private=True,
        )

        repo.add(calendar)
        db.session.commit()

        loaded = repo.get(calendar.id)
        assert loaded.admin_unit_id == admin_unit_id
        assert loaded.name == "Sports"
        assert loaded.description == "Text"
        assert loaded.private is True

        calendar.update(actor=actor, name="Renamed", description=None, private=False)
        repo.update(calendar)
        db.session.commit()

        loaded = repo.get(calendar.id)
        assert loaded.name == "Renamed"
        assert loaded.description is None
        assert loaded.private is False

        repo.remove(calendar)
        db.session.commit()
        assert repo.get(calendar.id) is None


def test_get_unknown_returns_none(app, db):
    with app.app_context():
        assert SqlAlchemyCalendarRepository(db.session).get(-1) is None


def test_get_by_admin_unit_and_name_ignores_case(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    other_user_id, other_admin_unit_id = seeder.setup_base(
        email="other@test.de", name="Andere Crew", log_in=False
    )
    seeder.create_calendar(admin_unit_id, "Sports")
    with app.app_context():
        repo = SqlAlchemyCalendarRepository(db.session)

        assert repo.get_by_admin_unit_and_name(admin_unit_id, "sPORTS").name == "Sports"
        assert repo.get_by_admin_unit_and_name(admin_unit_id, "Music") is None
        assert repo.get_by_admin_unit_and_name(other_admin_unit_id, "Sports") is None


def test_duplicate_name_raises_duplicate_error(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    actor = Actor(user_id=user_id)
    seeder.create_calendar(admin_unit_id, "Sports")
    with app.app_context():
        repo = SqlAlchemyCalendarRepository(db.session)

        with pytest.raises(DuplicateError):
            repo.add(
                CalendarAggregate.create(
                    actor=actor, admin_unit_id=admin_unit_id, name="Sports"
                )
            )


def test_entries_are_added_and_removed(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    actor = Actor(user_id=user_id)
    calendar_id = seeder.create_calendar(admin_unit_id)
    event_id = seeder.create_event(admin_unit_id)
    with app.app_context():
        repo = SqlAlchemyCalendarEntryRepository(db.session)
        entry = CalendarEntryAggregate.create(actor, calendar_id, event_id)

        repo.add(entry)
        db.session.commit()

        loaded = repo.get(entry.id)
        assert (loaded.calendar_id, loaded.event_id) == (calendar_id, event_id)

        repo.remove(entry)
        db.session.commit()
        assert repo.get(entry.id) is None


def test_deleting_calendar_event_and_organization_removes_entries(app, db, seeder):
    from project.infrastructure.models import AdminUnit, CalendarEntry, Event

    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    calendar_id = seeder.create_calendar(admin_unit_id, "A")
    other_calendar_id = seeder.create_calendar(admin_unit_id, "B")
    event_id = seeder.create_event(admin_unit_id)
    other_event_id = seeder.create_event(admin_unit_id, name="Other")
    seeder.create_calendar_entry(calendar_id, event_id)
    seeder.create_calendar_entry(other_calendar_id, event_id)
    seeder.create_calendar_entry(other_calendar_id, other_event_id)

    with app.app_context():
        db.session.delete(db.session.get(Event, event_id))
        db.session.commit()
        assert CalendarEntry.query.count() == 1

        db.session.delete(db.session.get(AdminUnit, admin_unit_id))
        db.session.commit()
        assert CalendarEntry.query.count() == 0


def test_entry_finders(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    other_user_id, other_admin_unit_id = seeder.setup_base(
        email="other@test.de", name="Andere Crew", log_in=False
    )
    own_calendar = seeder.create_calendar(admin_unit_id, "Own")
    foreign_calendar = seeder.create_calendar(other_admin_unit_id, "Foreign")
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_calendar_entry(own_calendar, event_id)
    seeder.create_calendar_entry(foreign_calendar, event_id)

    with app.app_context():
        repo = SqlAlchemyCalendarEntryRepository(db.session)

        assert (
            repo.get_by_calendar_and_event(own_calendar, event_id).event_id == event_id
        )
        assert repo.get_by_calendar_and_event(own_calendar, 4711) is None
        own = repo.get_by_event_and_admin_unit(event_id, admin_unit_id)
        assert [entry.calendar_id for entry in own] == [own_calendar]
        assert repo.get_by_event_and_admin_unit(event_id, 4711) == []
