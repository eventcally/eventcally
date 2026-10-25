from project.domain.events.event_organizer_created import EventOrganizerCreated
from project.domain.events.event_organizer_updated import EventOrganizerUpdated
from project.domain.models.aggregates.event_organizer_aggregate import (
    EventOrganizerAggregate,
)
from project.domain.models.entities.actor import Actor
from project.domain.models.entities.image_entity import ImageEntity
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.infrastructure.models.event_organizer import EventOrganizer
from project.infrastructure.repositories.sql_alchemy_event_organizer_repository import (
    SqlAlchemyEventOrganizerRepository,
)


def _logo(data=b"organizer-logo"):
    return ImageEntity.model_construct(
        id=-1,
        hash=1,
        data=data,
        encoding_format="image/png",
        copyright_text="Copyright",
        license_id=None,
    )


def test_add_get_roundtrip_with_logo_and_location(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    with app.app_context():
        repo = SqlAlchemyEventOrganizerRepository(db.session)
        organizer = EventOrganizerAggregate.create(
            actor=Actor(user_id=user_id),
            admin_unit_id=admin_unit_id,
            name="Logo Organizer",
            url="https://example.com",
            email="organizer@example.com",
            phone="123",
            fax="456",
            location=LocationValueObject(city="Berlin", country="DE"),
            logo=_logo(),
        )

        repo.add(organizer)
        db.session.commit()

        loaded = repo.get(organizer.id)
        model = db.session.get(EventOrganizer, organizer.id)
        created_event = organizer.get_first_domain_event_by_type(EventOrganizerCreated)

        assert loaded.name == "Logo Organizer"
        assert loaded.url == "https://example.com"
        assert loaded.email == "organizer@example.com"
        assert loaded.phone == "123"
        assert loaded.fax == "456"
        assert loaded.location.city == "Berlin"
        assert loaded.logo.id == model.logo.id
        assert loaded.logo.data == b"organizer-logo"
        assert organizer.logo.id == model.logo.id
        assert created_event.id == organizer.id
        assert created_event.logo.id == model.logo.id
        assert created_event.logo.hash == model.logo.get_hash()


def test_add_without_logo_and_get_unknown(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    with app.app_context():
        repo = SqlAlchemyEventOrganizerRepository(db.session)
        organizer = EventOrganizerAggregate.create(
            actor=Actor(user_id=user_id),
            admin_unit_id=admin_unit_id,
            name="Plain Organizer",
        )

        repo.add(organizer)
        db.session.commit()

        loaded = repo.get(organizer.id)
        assert loaded.logo is None
        assert loaded.location is None
        assert repo.get(-1) is None


def test_update_logo_and_location_then_clear_and_remove(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    actor = Actor(user_id=user_id)
    with app.app_context():
        repo = SqlAlchemyEventOrganizerRepository(db.session)
        organizer = EventOrganizerAggregate.create(
            actor=actor, admin_unit_id=admin_unit_id, name="Update Organizer"
        )
        repo.add(organizer)
        db.session.commit()

        organizer.update(
            actor=actor,
            name="Updated Organizer",
            location=LocationValueObject(city="Hamburg", country="DE"),
            logo=_logo(b"new-logo"),
        )
        repo.update(organizer)
        db.session.commit()

        model = db.session.get(EventOrganizer, organizer.id)
        updated_event = organizer.get_first_domain_event_by_type(EventOrganizerUpdated)
        assert model.name == "Updated Organizer"
        assert model.location.city == "Hamburg"
        assert organizer.logo.id == model.logo.id
        assert updated_event.logo.old is None
        assert updated_event.logo.new.id == model.logo.id
        assert updated_event.logo.new.hash == model.logo.get_hash()

        organizer.update(actor=actor, location=None, logo=None)
        repo.update(organizer)
        db.session.commit()

        db.session.expire_all()
        model = db.session.get(EventOrganizer, organizer.id)
        assert model.logo is None
        assert model.location is None

        repo.remove(organizer)
        db.session.commit()
        assert repo.get(organizer.id) is None


def test_update_without_logo_change_keeps_logo_id(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    actor = Actor(user_id=user_id)
    with app.app_context():
        repo = SqlAlchemyEventOrganizerRepository(db.session)
        organizer = EventOrganizerAggregate.create(
            actor=actor,
            admin_unit_id=admin_unit_id,
            name="Keep Logo",
            logo=_logo(),
        )
        repo.add(organizer)
        db.session.commit()

        organizer.update(actor=actor, name="Keep Logo 2")
        repo.update(organizer)
        db.session.commit()

        model = db.session.get(EventOrganizer, organizer.id)
        assert model.name == "Keep Logo 2"
        assert organizer.logo.id == model.logo.id
