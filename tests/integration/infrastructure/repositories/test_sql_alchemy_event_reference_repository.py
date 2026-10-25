from project.domain.models.aggregates.event_reference_aggregate import (
    EventReferenceAggregate,
)
from project.domain.models.entities.actor import Actor
from project.infrastructure.models.event_reference import EventReference
from project.infrastructure.repositories.sql_alchemy_event_reference_repository import (
    SqlAlchemyEventReferenceRepository,
)


def _setup(seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    event_id = seeder.create_event(admin_unit_id)
    return Actor(user_id=user_id), other_admin_unit_id, event_id


def test_add_get_update_remove(app, db, seeder):
    actor, other_admin_unit_id, event_id = _setup(seeder)
    with app.app_context():
        repo = SqlAlchemyEventReferenceRepository(db.session)
        reference = EventReferenceAggregate.create(
            actor=actor,
            admin_unit_id=other_admin_unit_id,
            event_id=event_id,
            rating=70,
        )

        repo.add(reference)
        db.session.commit()

        loaded = repo.get(reference.id)
        assert loaded.admin_unit_id == other_admin_unit_id
        assert loaded.event_id == event_id
        assert loaded.rating == 70

        reference.update(actor=actor, rating=20)
        repo.update(reference)
        db.session.commit()

        assert db.session.get(EventReference, reference.id).rating == 20

        repo.remove(reference)
        db.session.commit()
        assert repo.get(reference.id) is None


def test_get_by_event_id_and_by_event_and_admin_unit(app, db, seeder):
    actor, other_admin_unit_id, event_id = _setup(seeder)
    with app.app_context():
        repo = SqlAlchemyEventReferenceRepository(db.session)
        reference = EventReferenceAggregate.create(
            actor=actor, admin_unit_id=other_admin_unit_id, event_id=event_id
        )
        repo.add(reference)
        db.session.commit()

        by_event = repo.get_by_event_id(event_id)
        assert [r.id for r in by_event] == [reference.id]
        assert repo.get_by_event_id(-1) == []

        by_pair = repo.get_by_event_and_admin_unit(event_id, other_admin_unit_id)
        assert by_pair.id == reference.id
        assert repo.get_by_event_and_admin_unit(event_id, -1) is None
