from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from project.domain.events.event_created import EventCreated
from project.domain.events.event_updated import EventUpdated
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.entities.image_entity import ImageEntity
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.infrastructure.models.event import Event
from project.infrastructure.repositories.sql_alchemy_event_repository import (
    SqlAlchemyEventRepository,
)


def _photo(data=b"event-photo"):
    return ImageEntity.model_construct(
        id=-1,
        hash=1,
        data=data,
        encoding_format="image/png",
        copyright_text="Copyright",
        license_id=None,
    )


def _date_definition(days=1):
    start = datetime.now(ZoneInfo("UTC")) + timedelta(days=days)
    return EventDateDefinitionValueObject(start=start)


def test_add_with_photo_sets_ids_on_aggregate_and_event(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    with app.app_context():
        repo = SqlAlchemyEventRepository(db.session)
        event = EventAggregate.create(
            actor=Actor(user_id=user_id),
            admin_unit_id=admin_unit_id,
            name="Photo Event",
            organizer_id=seeder.upsert_default_event_organizer(admin_unit_id),
            event_place_id=seeder.upsert_default_event_place(admin_unit_id),
            date_definitions=[_date_definition()],
            status=EventStatus.scheduled,
            public_status=EventPublicStatus.published,
            photo=_photo(),
        )

        repo.add(event)
        db.session.commit()

        model = db.session.get(Event, event.id)
        created = event.get_first_domain_event_by_type(EventCreated)
        assert event.photo.id == model.photo.id
        assert created.photo.id == model.photo.id
        assert created.photo.hash == model.photo.get_hash()
        assert event.dates[0].id == model.dates[0].id
        assert repo.get(event.id).photo.id == model.photo.id


def test_update_photo_and_dates_assigns_ids(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    actor = Actor(user_id=user_id)
    with app.app_context():
        repo = SqlAlchemyEventRepository(db.session)
        event = repo.get(event_id)

        event.update(
            actor=actor,
            photo=_photo(b"new-photo"),
            date_definitions=[_date_definition(days=5), _date_definition(days=6)],
        )
        repo.update(event)
        db.session.commit()

        model = db.session.get(Event, event_id)
        updated = event.get_first_domain_event_by_type(EventUpdated)
        assert event.photo.id == model.photo.id
        assert updated.photo.new.id == model.photo.id
        assert updated.photo.new.hash == model.photo.get_hash()
        assert {d.id for d in event.dates} == {d.id for d in model.dates}
        assert len(model.dates) == 2


def test_remove_deletes_the_event(app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    with app.app_context():
        repo = SqlAlchemyEventRepository(db.session)
        event = repo.get(event_id)

        repo.remove(event)
        db.session.commit()

        assert repo.get(event_id) is None
