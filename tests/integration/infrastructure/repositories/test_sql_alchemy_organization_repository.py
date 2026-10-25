from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.entities.actor import Actor
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.infrastructure.repositories.sql_alchemy_organization_repository import (
    SqlAlchemyOrganizationRepository,
)


def test_add_get_update_remove(app, db, seeder):
    user_id, _ = seeder.setup_base(log_in=False)
    actor = Actor(user_id=user_id)
    with app.app_context():
        repo = SqlAlchemyOrganizationRepository(db.session)
        organization = OrganizationAggregate.create(
            actor=actor,
            name="Repo Organization",
            short_name="repoorg",
            location=LocationValueObject(city="Berlin", country="DE"),
        )

        repo.add(organization)
        db.session.commit()

        loaded = repo.get(organization.id)
        assert loaded.name == "Repo Organization"
        assert loaded.location.city == "Berlin"

        organization.update(actor=actor, name="Renamed", description="Description")
        repo.update(organization)
        db.session.commit()

        loaded = repo.get(organization.id)
        assert loaded.name == "Renamed"
        assert loaded.description == "Description"

        repo.remove(organization)
        db.session.commit()
        assert repo.get(organization.id) is None
        assert repo.get(-1) is None
